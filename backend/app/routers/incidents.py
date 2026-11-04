from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from ..db import get_db, Incident
from ..services.sessions import incident_to_dict
from pydantic import BaseModel

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

class StatusUpdate(BaseModel):
    status: str

@router.get("")
def list_incidents(status: str = None, severity: str = None, machine_id: str = None, q: str = None, db: Session = Depends(get_db)):
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if severity:
        query = query.filter(Incident.severity == severity)
    if machine_id:
        query = query.filter(Incident.machine_id == machine_id)
    items = query.order_by(Incident.created_at.desc()).all()
    out = [incident_to_dict(i) for i in items]
    if q:
        ql = q.lower()
        out = [i for i in out if ql in (i.get("description") or "").lower() or ql in (i.get("machine_id") or "").lower() or ql in (i.get("plant_area") or "").lower()]
    return out

@router.get("/{iid}")
def get_incident(iid: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == iid).first()
    if not inc:
        raise HTTPException(404, "not found")
    return incident_to_dict(inc)

@router.patch("/{iid}")
def update_incident(iid: str, payload: StatusUpdate, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == iid).first()
    if not inc:
        raise HTTPException(404, "not found")
    inc.status = payload.status
    from datetime import datetime as _dt
    inc.updated_at = _dt.utcnow()
    db.commit()
    db.refresh(inc)
    return incident_to_dict(inc)

@router.delete("/{iid}")
def delete_incident(iid: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == iid).first()
    if not inc:
        raise HTTPException(404, "not found")
    db.delete(inc)
    db.commit()
    return {"deleted": True}
