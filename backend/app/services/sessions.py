import uuid, json
from datetime import datetime
from sqlalchemy.orm import Session
from ..db import Incident
from .llm import extract as llm_extract, generate_handover_summary

SESSIONS = {}

def new_session_id():
    return str(uuid.uuid4())

async def start_session(transcript: str):
    sid = new_session_id()
    result = await llm_extract(transcript)
    SESSIONS[sid] = {
        "id": sid,
        "transcript": transcript,
        "fields": result["fields"],
        "missing_fields": result["missing_fields"],
        "confidence": result["confidence"],
        "questions": result["questions"],
        "answers": [],
        "status": "awaiting_followup" if result["questions"] else "ready_for_confirmation",
        "source": result.get("source"),
        "created_at": datetime.utcnow().isoformat()+"Z",
    }
    # if no questions, ready
    if not result["questions"]:
        SESSIONS[sid]["status"] = "ready_for_confirmation"
    return SESSIONS[sid]

def get_session(sid):
    return SESSIONS.get(sid)

async def answer_session(sid: str, answer: str):
    s = SESSIONS.get(sid)
    if not s:
        return None
    s["answers"].append(answer)
    # merge answer into transcript and re-extract? Simpler: append to description
    s["transcript"] = s["transcript"] + " " + answer
    result = await llm_extract(s["transcript"])
    s["fields"] = result["fields"]
    s["missing_fields"] = result["missing_fields"]
    s["confidence"] = result["confidence"]
    # regenerate questions but avoid repeats
    qs = result["questions"]
    # remove questions already answered crudely: keep up to 2
    s["questions"] = qs[:2]
    if not s["questions"] or len(s["answers"]) >= 3:
        s["status"] = "ready_for_confirmation"
    else:
        s["status"] = "awaiting_followup"
    return s

def build_confirmation(s):
    f = s["fields"]
    return {
        "session_id": s["id"],
        "transcript": s["transcript"],
        "fields": f,
        "missing_fields": s["missing_fields"],
        "confidence": s["confidence"],
        "status": s["status"],
    }

def confirm_session(sid: str, edited_fields: dict, db: Session):
    s = SESSIONS.get(sid)
    if not s:
        return None
    f = dict(s["fields"])
    f.update(edited_fields or {})
    inc_id = "INC-" + str(uuid.uuid4())[:8].upper()
    inc = Incident(
        id=inc_id,
        machine_id=f.get("machine_id"),
        plant_area=f.get("plant_area"),
        description=f.get("description"),
        category=f.get("category"),
        severity=f.get("severity"),
        occurred_at=f.get("occurred_at"),
        sensor_readings=json.dumps(f.get("sensor_readings") or []),
        actions_taken=json.dumps(f.get("actions_taken") or []),
        missing_info=json.dumps(s.get("missing_fields") or []),
        recommended_next_steps=json.dumps(recommended_steps(f, s.get("missing_fields") or [])),
        status="open",
        confirmation_status="confirmed",
        transcript=s["transcript"],
        confidence=s["confidence"],
        confirmed_at=datetime.utcnow(),
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)
    s["status"] = "confirmed"
    s["incident_id"] = inc_id
    return inc

def recommended_steps(fields, missing):
    steps = []
    sev = fields.get("severity")
    if sev in ("critical","high"):
        steps.append("Notify maintenance supervisor immediately.")
    if "machine_id" in missing or not fields.get("machine_id"):
        steps.append("Identify and record the affected machine ID.")
    if "sensor_readings" in missing or not fields.get("sensor_readings"):
        steps.append("Capture current sensor readings for diagnosis.")
    steps.append("Inspect machine and document findings.")
    if sev in ("critical","high"):
        steps.append("Consider isolating machine until inspected.")
    return steps

def incident_to_dict(inc: Incident):
    return {
        "id": inc.id,
        "machine_id": inc.machine_id,
        "plant_area": inc.plant_area,
        "description": inc.description,
        "category": inc.category,
        "severity": inc.severity,
        "occurred_at": inc.occurred_at,
        "sensor_readings": json.loads(inc.sensor_readings) if inc.sensor_readings else [],
        "actions_taken": json.loads(inc.actions_taken) if inc.actions_taken else [],
        "missing_info": json.loads(inc.missing_info) if inc.missing_info else [],
        "recommended_next_steps": json.loads(inc.recommended_next_steps) if inc.recommended_next_steps else [],
        "status": inc.status,
        "confirmation_status": inc.confirmation_status,
        "transcript": inc.transcript,
        "confidence": inc.confidence,
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
        "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
        "confirmed_at": inc.confirmed_at.isoformat() if inc.confirmed_at else None,
    }
