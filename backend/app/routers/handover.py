from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db, Incident
from ..services.sessions import incident_to_dict
from ..services.llm import generate_handover_summary

router = APIRouter(prefix="/api/handover", tags=["handover"])

@router.get("")
async def handover(db: Session = Depends(get_db)):
    items = db.query(Incident).order_by(Incident.created_at.desc()).limit(50).all()
    dicts = [incident_to_dict(i) for i in items]
    summary = await generate_handover_summary(dicts)
    return {"summary": summary, "count": len(dicts)}
