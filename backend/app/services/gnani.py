import base64
import httpx
import asyncio
from ..config import (
    GNANI_API_KEY_ID, GNANI_API_KEY_SECRET, GNANI_STT_URL, GNANI_TTS_URL,
    GNANI_TTS_VOICE, GNANI_TTS_MODEL,
)

MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB
SUPPORTED_LANGS = ["hi-IN", "en-IN", "ta-IN", "te-IN", "bn-IN", "kn-IN", "mr-IN", "gu-IN", "pa-IN", "ml-IN"]

def _headers():
    h = {}
    if GNANI_API_KEY_ID:
        h["X-API-Key-ID"] = GNANI_API_KEY_ID
    if GNANI_API_KEY_SECRET:
        h["X-API-Key-Secret"] = GNANI_API_KEY_SECRET
    return h

def gnani_configured() -> bool:
    return bool(GNANI_API_KEY_ID)

async def _retry(coro_factory, attempts=3, base_delay=1.0):
    last = None
    for i in range(attempts):
        try:
            return await coro_factory()
        except Exception as e:
            last = e
            if i < attempts - 1:
                await asyncio.sleep(base_delay * (2 ** i))
    raise last

async def transcribe(audio_bytes: bytes, filename: str = "audio.wav", language_code: str = "hi-IN") -> dict:
    if not gnani_configured():
        return {"success": False, "error": "GNANI_API_KEY_ID not configured. Set it in backend/.env to enable live transcription.", "transcript": "", "provider": "gnani-prisma", "live": False}
    if not audio_bytes:
        return {"success": False, "error": "Empty audio payload.", "transcript": "", "provider": "gnani-prisma", "live": False}
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        return {"success": False, "error": f"Audio too large ({len(audio_bytes)} bytes). Max {MAX_AUDIO_BYTES}.", "transcript": "", "provider": "gnani-prisma", "live": False}
    if language_code not in SUPPORTED_LANGS:
        language_code = "hi-IN"

    async def _do():
        files = {"audio_file": (filename, audio_bytes)}
        data = {
            "language_code": language_code,
            "preferred_language": language_code,
            "format": "transcribe",
            "itn_native_numerals": "true",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(GNANI_STT_URL, data=data, files=files, headers=_headers())
        if r.status_code == 429:
            raise RuntimeError("Rate limited by Gnani STT")
        if r.status_code >= 500:
            raise RuntimeError(f"Gnani STT server error {r.status_code}")
        if r.status_code != 200:
            return {"success": False, "error": f"STT HTTP {r.status_code}: {r.text[:300]}", "transcript": "", "provider": "gnani-prisma", "live": True}
        try:
            j = r.json()
        except Exception:
            return {"success": False, "error": f"Non-JSON response: {r.text[:300]}", "transcript": "", "provider": "gnani-prisma", "live": True}
        transcript = j.get("transcript") or j.get("text") or j.get("transcription") or ""
        return {"success": bool(j.get("success", True)) and bool(transcript), "transcript": transcript, "raw": j, "provider": "gnani-prisma", "live": True, "request_id": j.get("request_id")}

    try:
        return await _retry(_do)
    except Exception as e:
        return {"success": False, "error": f"STT failed after retries: {e}", "transcript": "", "provider": "gnani-prisma", "live": True}

async def synthesize(text: str) -> dict:
    if not gnani_configured():
        return {"success": False, "error": "GNANI_API_KEY_ID not configured.", "audio_base64": "", "mime": "audio/mpeg", "provider": "gnani-timbre", "live": False}
    if not text or not text.strip():
        return {"success": False, "error": "Empty text for TTS.", "audio_base64": "", "mime": "audio/mpeg", "provider": "gnani-timbre", "live": True}
    text = text.strip()[:4000]

    async def _do():
        payload = {
            "audio_config": {
                "bitrate": "192k",
                "container": "mp3",
                "encoding": "linear_pcm",
                "num_channels": 1,
                "sample_rate": 44100,
                "sample_width": 2,
            },
            "model": GNANI_TTS_MODEL,
            "text": text,
            "voice": GNANI_TTS_VOICE,
        }
        headers = _headers()
        headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(GNANI_TTS_URL, json=payload, headers=headers)
        if r.status_code == 429:
            raise RuntimeError("Rate limited by Gnani TTS")
        if r.status_code >= 500:
            raise RuntimeError(f"Gnani TTS server error {r.status_code}")
        if r.status_code != 200:
            return {"success": False, "error": f"TTS HTTP {r.status_code}: {r.text[:300]}", "audio_base64": "", "mime": "audio/mpeg", "provider": "gnani-timbre", "live": True}
        audio_chunks = []
        for line in r.text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data or data.startswith("{"):
                continue
            try:
                audio_chunks.append(base64.b64decode(data))
            except Exception:
                pass
        audio = b"".join(audio_chunks) or r.content
        if not audio:
            return {"success": False, "error": "No audio returned by TTS.", "audio_base64": "", "mime": "audio/mpeg", "provider": "gnani-timbre", "live": True}
        b64 = base64.b64encode(audio).decode()
        return {"success": True, "audio_base64": b64, "mime": "audio/mpeg", "bytes": len(audio), "provider": "gnani-timbre", "live": True}

    try:
        return await _retry(_do)
    except Exception as e:
        return {"success": False, "error": f"TTS failed after retries: {e}", "audio_base64": "", "mime": "audio/mpeg", "provider": "gnani-timbre", "live": True}
