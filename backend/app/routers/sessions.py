from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.sessions import start_session, get_session, answer_session, build_confirmation, confirm_session
from ..db import get_db
from fastapi import Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

class StartReq(BaseModel):
    transcript: str

class AnswerReq(BaseModel):
    answer: str

class ConfirmReq(BaseModel):
    edited_fields: dict = {}

@router.post("/start")
async def start(req: StartReq):
    s = await start_session(req.transcript)
    return s

@router.get("/{sid}")
def get(sid: str):
    s = get_session(sid)
    if not s:
        raise HTTPException(404, "session not found")
    return s

@router.post("/{sid}/answer")
async def answer(sid: str, req: AnswerReq):
    s = await answer_session(sid, req.answer)
    if not s:
        raise HTTPException(404, "session not found")
    return s

@router.get("/{sid}/confirmation")
def confirmation(sid: str):
    s = get_session(sid)
    if not s:
        raise HTTPException(404, "session not found")
    return build_confirmation(s)

@router.post("/{sid}/confirm")
def confirm(sid: str, req: ConfirmReq, db: Session = Depends(get_db)):
    inc = confirm_session(sid, req.edited_fields, db)
    if not inc:
        raise HTTPException(404, "session not found")
    from ..services.sessions import incident_to_dict
    return incident_to_dict(inc)
