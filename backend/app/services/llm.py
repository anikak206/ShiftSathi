import json, re, os
from datetime import datetime
from ..config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

REQUIRED_FIELDS = ["machine_id", "severity", "occurred_at", "plant_area", "description"]

CATEGORIES = {
    "vibration": ["vibration", "vibrat", "kaanp", "kaanpna"],
    "leak": ["leak", "leakage", "drip", "spill", "tel", "oil"],
    "overheating": ["overheat", "hot", "temperature", "garmi", "garam", "heat"],
    "noise": ["noise", "sound", "awaz", "shor", "grinding", "rattling"],
    "electrical": ["electrical", "spark", "current", "voltage", "short", "power"],
    "mechanical": ["bearing", "gear", "belt", "motor", "pump", "valve"],
    "safety": ["fire", "smoke", "accident", "injury", "danger"],
}

SEVERITY_WORDS = {
    "critical": ["fire", "explosion", "smoke", "accident", "injury", "danger", "critical", "emergency", "band", "stopped production"],
    "high": ["leak", "overheat", "not working", "down", "urgent", "high", "severe", "breakdown"],
    "medium": ["vibration", "noise", "unusual", "abnormal", "medium", "moderate"],
    "low": ["minor", "slight", "small", "low", "routine"],
}

def _classify_category(text):
    t = text.lower()
    for cat, words in CATEGORIES.items():
        if any(w in t for w in words):
            return cat
    return "general"

def _classify_severity(text):
    t = text.lower()
    for sev in ["critical", "high", "medium", "low"]:
        if any(w in t for w in SEVERITY_WORDS[sev]):
            return sev
    return "medium"

def _extract_machine_id(text):
    patterns = [
        r"machine\s*(?:number|no\.?|#)?\s*([a-zA-Z0-9\-]+)",
        r"machine\s*([0-9]+)",
        r"m/c\s*([a-zA-Z0-9\-]+)",
        r"equipment\s*(?:id|number)?\s*([a-zA-Z0-9\-]+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            # normalize number words
            return _normalize_number_word(val)
    # number words
    word_nums = {"one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9","ten":"10",
                 "ek":"1","do":"2","teen":"3","char":"4","paanch":"5","chhe":"6"," saat":"7","aath":"8","nau":"9","das":"10"}
    for w, n in word_nums.items():
        m = re.search(r"machine\s*(?:number|no\.?)?\s*" + w, text, re.IGNORECASE)
        if m:
            return n
    return None

def _normalize_number_word(val):
    word_nums = {"one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9","ten":"10",
                 "ek":"1","do":"2","teen":"3","char":"4","paanch":"5","paach":"5","chhe":"6","saat":"7","aath":"8","nau":"9","das":"10"}
    v = val.lower().strip()
    return word_nums.get(v, val)

def _extract_sensor_readings(text):
    readings = []
    # number + unit
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(°c|celsius|deg|degrees|rpm|bar|psi|amp|amps|volt|volts|hz|khz|mm|cm|m/s|lpm|g)\b", text, re.IGNORECASE):
        readings.append(f"{m.group(1)} {m.group(2)}")
    # generic "reading X"
    for m in re.finditer(r"reading[s]?\s*(?:of|is|:)?\s*([0-9][0-9., ]*)", text, re.IGNORECASE):
        readings.append(m.group(1).strip())
    return list(dict.fromkeys(readings))

def _extract_actions(text):
    t = text.lower()
    actions = []
    keywords = ["stopped", "band kar", "band kar diya", "shut down", "shutdown", "restarted", "restart", "cleaned", "checked", "inspected", "isolated", "locked out", "tagged", "reported", "called maintenance", "informed supervisor"]
    for k in keywords:
        if k in t:
            actions.append(k)
    return actions

def _extract_plant_area(text):
    m = re.search(r"(?:in|at|on)\s+(?:the\s+)?([A-Za-z][A-Za-z0-9 \-]{2,40}?)(?:\s+(?:area|section|line|plant|floor|shop))", text, re.IGNORECASE)
    if m:
        return m.group(1).strip() + " " + (re.search(r"(?:area|section|line|plant|floor|shop)", text, re.IGNORECASE).group(0) if re.search(r"(?:area|section|line|plant|floor|shop)", text, re.IGNORECASE) else "")
    m = re.search(r"(?:plant|area|section|line|floor|shop)\s*[:\-]?\s*([A-Za-z0-9 \-]{2,30})", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None

def heuristic_extract(transcript: str) -> dict:
    text = transcript.strip()
    machine_id = _extract_machine_id(text)
    category = _classify_category(text)
    severity = _classify_severity(text)
    readings = _extract_sensor_readings(text)
    actions = _extract_actions(text)
    plant_area = _extract_plant_area(text)
    occurred_at = datetime.utcnow().isoformat() + "Z"
    # if mentions time
    tm = re.search(r"(?:since|from|at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|baje)?)", text, re.IGNORECASE)
    if tm:
        occurred_at = tm.group(1).strip() + " (reported)"
    missing = []
    if not machine_id:
        missing.append("machine_id")
    if not plant_area:
        missing.append("plant_area")
    if not severity or severity == "medium":
        # severity inferred; not missing but low confidence
        pass
    if not readings:
        missing.append("sensor_readings")
    # occurred_at default present
    # description always present
    fields = {
        "machine_id": machine_id,
        "plant_area": plant_area,
        "description": text,
        "category": category,
        "severity": severity,
        "occurred_at": occurred_at,
        "sensor_readings": readings,
        "actions_taken": actions,
    }
    confidence = 0.5
    if machine_id: confidence += 0.15
    if plant_area: confidence += 0.1
    if readings: confidence += 0.1
    if actions: confidence += 0.05
    confidence = min(0.95, round(confidence, 2))
    questions = generate_followup_questions(fields, missing)
    return {
        "fields": fields,
        "missing_fields": missing,
        "confidence": confidence,
        "questions": questions,
        "source": "heuristic",
    }

def generate_followup_questions(fields, missing):
    qs = []
    if "machine_id" in missing or not fields.get("machine_id"):
        qs.append("Which machine or equipment is affected? Please share the machine ID or number.")
    if "plant_area" in missing or not fields.get("plant_area"):
        qs.append("Which plant area, line, or section is this happening in?")
    if not fields.get("sensor_readings"):
        qs.append("Are there any abnormal readings (temperature, vibration, pressure, RPM)? If yes, please share them.")
    # contextual
    desc = (fields.get("description") or "").lower()
    if "vibration" in desc and "noise" not in desc:
        qs.append("Is there any unusual noise along with the vibration?")
    if "vibration" in desc:
        qs.append("When did the vibration begin, and is production currently affected?")
    if "leak" in desc:
        qs.append("Has the machine been stopped? Is there any safety risk or slip hazard?")
    if "overheat" in desc or "hot" in desc or "garam" in desc:
        qs.append("Has the machine been shut down to cool? Are there any smoke or burning smells?")
    if not fields.get("actions_taken"):
        qs.append("What actions have already been taken, if any?")
    # dedup
    seen = set(); out = []
    for q in qs:
        if q not in seen:
            seen.add(q); out.append(q)
    # limit to 4
    return out[:4]

async def extract(transcript: str) -> dict:
    if LLM_API_KEY:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
            system = """You are an industrial incident extraction assistant. Extract structured fields from a worker's spoken report (may be Hindi/English/Hinglish). Return ONLY valid JSON with keys:
machine_id (string or null), plant_area (string or null), description (string), category (one of: vibration, leak, overheating, noise, electrical, mechanical, safety, general), severity (critical|high|medium|low), occurred_at (string or null), sensor_readings (array of strings), actions_taken (array of strings), missing_fields (array of field names among: machine_id, plant_area, severity, occurred_at, sensor_readings), confidence (0-1 number), questions (array of concise follow-up question strings, max 4, only for missing/ambiguous info). Do not invent details. If unknown use null."""
            resp = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[{"role":"system","content":system},{"role":"user","content":transcript}],
                temperature=0.1,
                response_format={"type":"json_object"},
            )
            content = resp.choices[0].message.content
            data = json.loads(content)
            fields = {
                "machine_id": data.get("machine_id"),
                "plant_area": data.get("plant_area"),
                "description": data.get("description") or transcript,
                "category": data.get("category") or "general",
                "severity": data.get("severity") or "medium",
                "occurred_at": data.get("occurred_at") or datetime.utcnow().isoformat()+"Z",
                "sensor_readings": data.get("sensor_readings") or [],
                "actions_taken": data.get("actions_taken") or [],
            }
            missing = data.get("missing_fields") or []
            # ensure consistency
            for f in ["machine_id","plant_area"]:
                if not fields.get(f) and f not in missing:
                    missing.append(f)
            if not fields.get("sensor_readings") and "sensor_readings" not in missing:
                missing.append("sensor_readings")
            questions = data.get("questions") or generate_followup_questions(fields, missing)
            return {
                "fields": fields,
                "missing_fields": missing,
                "confidence": float(data.get("confidence") or 0.7),
                "questions": questions[:4],
                "source": "llm",
            }
        except Exception as e:
            # fallback
            res = heuristic_extract(transcript)
            res["llm_error"] = str(e)
            return res
    return heuristic_extract(transcript)

async def generate_handover_summary(incidents: list) -> str:
    if LLM_API_KEY and incidents:
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
            data = json.dumps(incidents, default=str)[:6000]
            resp = await client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role":"system","content":"You are an industrial shift supervisor assistant. Generate a concise shift handover summary from incidents. Include: new incidents, pending maintenance, high-priority/critical, actions completed, unresolved. Use bullet points. Be professional."},
                    {"role":"user","content":data},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content
        except Exception as e:
            pass
    # heuristic summary
    lines = ["Shift Handover Summary", "====================="]
    total = len(incidents)
    open_inc = [i for i in incidents if i.get("status") == "open"]
    crit = [i for i in incidents if i.get("severity") in ("critical","high")]
    lines.append(f"Total incidents: {total}")
    lines.append(f"Open incidents: {len(open_inc)}")
    lines.append(f"Critical/High priority: {len(crit)}")
    lines.append("")
    lines.append("Incidents:")
    for i in incidents:
        lines.append(f"- [{i.get('severity','?').upper()}] {i.get('machine_id') or 'Unknown machine'}: {i.get('description','')[:120]} (status: {i.get('status','open')})")
    lines.append("")
    lines.append("Recommended follow-up: Review all open and critical incidents with maintenance team.")
    return "\n".join(lines)
