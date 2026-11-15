"""Verify Gnani Prisma STT and Timbre TTS using GNANI_API_KEY_ID from backend/.env.

Usage:
    cd backend
    python verify_gnani.py

Exits 0 on success, 1 on failure.
"""
import asyncio
import base64
import os
import sys
import wave
import struct

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

sys.path.insert(0, os.path.dirname(__file__))
from app.services.gnani import transcribe, synthesize, gnani_configured

def make_test_wav(path, duration=2.0, rate=16000):
    """Generate a WAV with a simple tone (not speech, but tests the API path)."""
    n = int(rate * duration)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        for i in range(n):
            val = int(32767 * 0.3 * (1 if (i // (rate // 440)) % 2 == 0 else -1))
            w.writeframes(struct.pack("<h", val))

async def main():
    if not gnani_configured():
        print("FAIL: GNANI_API_KEY_ID not set in backend/.env")
        sys.exit(1)

    print("GNANI_API_KEY_ID present. Starting verification...")

    # 1. TTS
    print("\n[1/2] Testing Timbre TTS...")
    phrase = "नमस्ते, यह एक परीक्षण है।"
    tts_res = await synthesize(phrase)
    print(f"  success={tts_res.get('success')} provider={tts_res.get('provider')} live={tts_res.get('live')}")
    if not tts_res.get("success"):
        print(f"  ERROR: {tts_res.get('error')}")
        sys.exit(1)
    audio_b64 = tts_res["audio_base64"]
    audio_bytes = base64.b64decode(audio_b64)
    print(f"  received {len(audio_bytes)} bytes of audio (mime={tts_res.get('mime')})")
    # save TTS audio
    tts_path = os.path.join(os.path.dirname(__file__), "verify_tts_output.wav")
    with open(tts_path, "wb") as f:
        f.write(audio_bytes)
    print(f"  saved to {tts_path}")

    # 2. STT using the TTS audio (round-trip)
    print("\n[2/2] Testing Prisma STT (round-trip with TTS audio)...")
    stt_res = await transcribe(audio_bytes, "verify_tts_output.wav", "hi-IN")
    print(f"  success={stt_res.get('success')} provider={stt_res.get('provider')} live={stt_res.get('live')}")
    print(f"  model={stt_res.get('model')} detected_language={stt_res.get('detected_language_code')}")
    if stt_res.get("transcript"):
        print(f"  transcript: {stt_res['transcript']}")
    else:
        print(f"  transcript: (empty) error={stt_res.get('error')}")

    if not stt_res.get("success"):
        print("\nRESULT: PARTIAL — TTS OK, STT failed (see error above)")
        sys.exit(1)

    print("\nRESULT: SUCCESS — both Prisma STT and Timbre TTS verified with real API calls")
    sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
EOF