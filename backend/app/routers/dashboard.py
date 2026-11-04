from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db, Incident
from sqlalchemy import func

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    total = db.query(Incident).count()
    open_c = db.query(Incident).filter(Incident.status == "open").count()
    resolved = db.query(Incident).filter(Incident.status == "resolved").count()
    critical = db.query(Incident).filter(Incident.severity.in_(["critical","high"])).count()
    # priority distribution
    dist = {}
    for sev in ["critical","high","medium","low"]:
        dist[sev] = db.query(Incident).filter(Incident.severity == sev).count()
    # by category
    cats = {}
    for (cat,) in db.query(Incident.category).distinct().all():
        cats[cat or "general"] = db.query(Incident).filter(Incident.category == cat).count()
    # recent
    recent = db.query(Incident).order_by(Incident.created_at.desc()).limit(5).all()
    from ..services.sessions import incident_to_dict
    return {
        "total": total,
        "open": open_c,
        "resolved": resolved,
        "critical": critical,
        "priority_distribution": dist,
        "category_distribution": cats,
        "recent": [incident_to_dict(i) for i in recent],
    }
