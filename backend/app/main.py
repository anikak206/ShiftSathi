from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import APP_NAME, CORS_ORIGINS, GNANI_API_KEY_ID, LLM_API_KEY
from .db import init_db
from .routers import voice, sessions, incidents, dashboard, handover, extract, eval

app = FastAPI(title=APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    import logging
    log = logging.getLogger("shiftsathi")
    if not GNANI_API_KEY_ID:
        log.warning("GNANI_API_KEY_ID not set; STT/TTS will run in fallback mode.")
    if not LLM_API_KEY:
        log.warning("LLM_API_KEY not set; using heuristic extraction.")

app.include_router(voice.router)
app.include_router(sessions.router)
app.include_router(incidents.router)
app.include_router(dashboard.router)
app.include_router(handover.router)
app.include_router(extract.router)
app.include_router(eval.router)

@app.get("/health")
def health():
    return {"status": "ok", "app": APP_NAME, "version": "1.0.0"}

@app.get("/health/detailed")
def health_detailed():
    from .config import GNANI_API_KEY_ID, LLM_API_KEY
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": "1.0.0",
        "gnani_configured": bool(GNANI_API_KEY_ID),
        "llm_configured": bool(LLM_API_KEY),
        "database": "sqlite",
    }
