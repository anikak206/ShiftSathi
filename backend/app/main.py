from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import APP_NAME, CORS_ORIGINS
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

app.include_router(voice.router)
app.include_router(sessions.router)
app.include_router(incidents.router)
app.include_router(dashboard.router)
app.include_router(handover.router)
app.include_router(extract.router)
app.include_router(eval.router)

@app.get("/health")
def health():
    return {"status": "ok", "app": APP_NAME}
