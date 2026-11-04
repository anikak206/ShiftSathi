import base64
import httpx
from ..config import (
    GNANI_API_KEY_ID, GNANI_API_KEY_SECRET, GNANI_STT_URL, GNANI_TTS_URL,
    GNANI_TTS_VOICE, GNANI_TTS_MODEL,
)

def _headers():
    h = {}
    if GNANI_API_KEY_ID:
        h["X-API-Key-ID"] = GNANI_API_KEY_ID
    if GNANI_API_KEY_SECRET:
        h["X-API-Key-Secret"] = GNANI_API_KEY_SECRET
    return h

async def transcribe(audio_bytes: bytes, filename: str = "audio.wav", language_code: str = "hi-IN") -> dict:
    if not GNANI_API_KEY_ID:
        return {"success": False, "error": "GNANI_API_KEY_ID not configured", "transcript": ""}
    try:
        files = {"audio_file": (filename, audio_bytes)}
        data = {
            "language_code": language_code,
            "preferred_language": language_code,
            "format": "transcribe",
            "itn_native_numerals": "true",
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(GNANI_STT_URL, data=data, files=files, headers=_headers())
        if r.status_code != 200:
            return {"success": False, "error": f"STT HTTP {r.status_code}: {r.text[:500]}", "transcript": ""}
        try:
            j = r.json()
        except Exception:
            return {"success": False, "error": f"Non-JSON response: {r.text[:500]}", "transcript": ""}
        transcript = j.get("transcript") or j.get("text") or ""
        return {"success": bool(j.get("success", True)), "transcript": transcript, "raw": j}
    except Exception as e:
        return {"success": False, "error": str(e), "transcript": ""}

async def synthesize(text: str) -> dict:
    if not GNANI_API_KEY_ID:
        return {"success": False, "error": "GNANI_API_KEY_ID not configured", "audio_base64": "", "mime": "audio/mpeg"}
    try:
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
        if r.status_code != 200:
            return {"success": False, "error": f"TTS HTTP {r.status_code}: {r.text[:500]}", "audio_base64": "", "mime": "audio/mpeg"}
        # Parse SSE
        audio_chunks = []
        for line in r.text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                data = line[5:].strip()
                if not data:
                    continue
                if data.startswith("{"):
                    continue
                try:
                    audio_chunks.append(base64.b64decode(data))
                except Exception:
                    pass
        audio = b"".join(audio_chunks)
        if not audio:
            # maybe response is raw binary
            audio = r.content
        b64 = base64.b64encode(audio).decode()
        return {"success": True, "audio_base64": b64, "mime": "audio/mpeg", "bytes": len(audio)}
    except Exception as e:
        return {"success": False, "error": str(e), "audio_base64": "", "mime": "audio/mpeg"}
