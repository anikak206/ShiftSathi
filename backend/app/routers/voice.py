from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ..services.gnani import transcribe, synthesize

router = APIRouter(prefix="/api/voice", tags=["voice"])

@router.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...), language_code: str = Form("hi-IN")):
    data = await file.read()
    res = await transcribe(data, file.filename or "audio.wav", language_code)
    return res

@router.post("/tts")
async def tts(payload: dict):
    text = payload.get("text", "")
    if not text:
        raise HTTPException(400, "text required")
    res = await synthesize(text)
    return res
