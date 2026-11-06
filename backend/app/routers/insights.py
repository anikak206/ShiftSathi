from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from collections import Counter
from ..db import get_db, Incident
from ..services.sessions import incident_to_dict

router = APIRouter(prefix="/api/insights", tags=["insights"])

@router.get("")
def insights(db: Session = Depends(get_db)):
    items = db.query(Incident).all()
    dicts = [incident_to_dict(i) for i in items]
    # recurring machines
    machine_counts = Counter(d.get("machine_id") for d in dicts if d.get("machine_id"))
    recurring = [{"machine_id": m, "count": c} for m, c in machine_counts.items() if c >= 2]
    recurring.sort(key=lambda x: -x["count"])
    # critical open
    crit_open = [d for d in dicts if d.get("severity") in ("critical", "high") and d.get("status") == "open"]
    # pending actions
    pending = []
    for d in dicts:
        if d.get("status") == "open":
            pending.extend(d.get("recommended_next_steps") or [])
    pending_counts = Counter(pending)
    # category distribution
    cat_counts = Counter(d.get("category") for d in dicts)
    return {
        "total_incidents": len(dicts),
        "recurring_machines": recurring,
        "open_critical": len(crit_open),
        "critical_incidents": crit_open[:10],
        "top_pending_actions": [{"action": a, "count": c} for a, c in pending_counts.most_common(5)],
        "category_counts": dict(cat_counts),
        "machines_affected": len(machine_counts),
    }
