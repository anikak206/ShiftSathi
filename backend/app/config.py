import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

def env(key, default=""):
    return os.getenv(key, default)

GNANI_API_KEY_ID = env("GNANI_API_KEY_ID", "")
GNANI_API_KEY_SECRET = env("GNANI_API_KEY_SECRET", "")
GNANI_STT_URL = env("GNANI_STT_URL", "https://api.vachana.ai/stt/v3")
GNANI_TTS_URL = env("GNANI_TTS_URL", "https://api.vachana.ai/api/v1/tts/sse")
GNANI_TTS_VOICE = env("GNANI_TTS_VOICE", "Karan")
GNANI_TTS_MODEL = env("GNANI_TTS_MODEL", "vachana-voice-v3")

LLM_API_KEY = env("LLM_API_KEY") or env("OPENAI_API_KEY", "")
LLM_BASE_URL = env("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = env("LLM_MODEL", "gpt-4o-mini")
LLM_PROVIDER = env("LLM_PROVIDER", "openai")

DATABASE_URL = env("DATABASE_URL", f"sqlite:///{(BASE_DIR / 'data' / 'shiftsathi.db').as_posix()}")
CORS_ORIGINS = [o.strip() for o in env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
APP_NAME = "ShiftSathi"
