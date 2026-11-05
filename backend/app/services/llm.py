import json, re, os
from datetime import datetime
from ..config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

REQUIRED_FIELDS = ["machine_id", "severity", "occurred_at", "plant_area", "description"]

CATEGORIES = {
    "safety": ["fire", "smoke", "accident", "injury", "danger", "evacuat", "explosion", "burst", "burning", "safety guard", "short", "safety concern", "safety"],
    "leak": ["leak", "leakage", "drip", "spill", "oil", "coolant", "hydraulic", "hose"],
    "overheating": ["overheat", "hot", "garmi", "garam", "heat", "over temp", "overheating"],
    "electrical": ["electrical", "spark", "current", "voltage", "power", "panel"],
    "noise": ["noise", "sound", "awaz", "shor", "grinding", "rattling", "cavitation"],
    "vibration": ["vibration", "vibrat", "kaanp"],
    "mechanical": ["bearing", "gear", "belt", "motor", "pump", "valve", "collision", "jam", "worn", "misalign", "broken", "tear", "stuck", "pneumatic", "pressure", "die"],
}

SEVERITY_WORDS = {
    "critical": ["fire", "explosion", "smoke", "accident", "injury", "danger", "critical", "emergency", "band", "stopped production"],
    "high": ["leak", "overheat", "not working", "down", "urgent", "high", "severe", "breakdown"],
    "medium": ["vibration", "noise", "unusual", "abnormal", "medium", "moderate"],
    "low": ["minor", "slight", "small", "low", "routine"],
}

def _classify_category(text):
    t = text.lower()
    # handle negations for safety keywords
    safe_text = t.replace("no injury", "").replace("no smoke", "").replace("no fire", "")
    for cat, words in CATEGORIES.items():
        if any(w in (safe_text if cat == "safety" else t) for w in words):
            return cat
    return "general"

def _classify_severity(text):
    t = text.lower().replace("no injury", "").replace("no smoke", "").replace("no fire", "")
    # critical
    if any(w in t for w in ["fire", "smoke", "explosion", "injury", "evacuat", "burst", "burning", "emergency", "safety guard missing", "machine isolated", "safety concern", "safety"]):
        return "critical"
    if "leak" in t and any(w in t for w in ["stopped", "burst", "floor", "spray"]):
        return "critical"
    if any(w in t for w in ["stopped", "shutdown", "down", "broken", "burst", "torn", "collision", "stopped immediately", "auto shutdown", "power off", "tripped"]):
        return "high"
    # overheating with high temperature
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:degree|deg|°)", t)
    if m and "overheat" in t and float(m.group(1)) >= 90:
        return "high"
    if any(w in t for w in ["minor", "slight", "small", "low", "routine", "scheduled", "normal", "within limits", "not critical", "no urgency"]):
        return "low"
    if any(w in t for w in ["leak", "overheat", "not working", "urgent", "severe", "high", "affected", "quality", "abnormal", "unusual"]):
        return "medium"
    return "medium"

_STOPWORDS = {"stopped", "stopping", "down", "running", "working", "ok", "fine", "checked", "inspected"}

def _extract_machine_id(text):
    # Prefer explicit equipment codes like P-12, M3, CNC-04
    for m in re.finditer(r"\b([A-Za-z]{1,4}[-_]?[0-9]{1,4})\b", text):
        cand = m.group(1)
        if cand.lower() not in _STOPWORDS:
            return cand
    # equipment noun(s) followed by id/number
    nouns = "machine|pump|motor|belt|conveyor|press|lathe|robot|furnace|boiler|compressor|cnc|spindle|gearbox|arm"
    m = re.search(r"(?:" + nouns + r")(?:\s+(?:" + nouns + r"))*\s*[#-]?\s*([A-Za-z0-9-]+)", text, re.IGNORECASE)
    if m:
        cand = m.group(1)
        if cand.lower() not in _STOPWORDS and not cand.isalpha():
            return _normalize_number_word(cand)
    # machine number X / machine X
    m = re.search(r"machine\s*(?:number|no\.?|#)?\s*([0-9]+|[a-zA-Z]+)", text, re.IGNORECASE)
    if m:
        val = m.group(1).strip()
        if val.lower() not in _STOPWORDS:
            return _normalize_number_word(val)
    # number words after "machine"
    word_nums = {"one":"1","two":"2","three":"3","four":"4","five":"5","six":"6","seven":"7","eight":"8","nine":"9","ten":"10",
                 "ek":"1","do":"2","teen":"3","char":"4","paanch":"5","paach":"5","chhe":"6","saat":"7","aath":"8","nau":"9","das":"10"}
    for w, n in word_nums.items():
        if re.search(r"machine\s*(?:number|no\.?)?\s*" + w + r"\b", text, re.IGNORECASE):
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
    # temperature extraction
    temp = None
    tm = re.search(r"(\d+(?:\.\d+)?)\s*(?:degree|deg|°)\s*(?:c|celsius)?", text, re.IGNORECASE)
    if tm:
        temp = tm.group(1) + "°C"
    # duration
    dur = None
    dm = re.search(r"(since|from|for)\s+(yesterday|today|last (?:night|week|month)|\d+\s*(?:hour|day|minute)s?)", text, re.IGNORECASE)
    if dm:
        dur = dm.group(0).strip()
    # operational impact
    impact = None
    if "production" in text.lower() and ("affected" in text.lower() or "stopped" in text.lower() or "down" in text.lower()):
        impact = "Production affected" if "affected" in text.lower() else "Production stopped" if "stopped" in text.lower() or "down" in text.lower() else None
    fields = {
        "machine_id": machine_id,
        "plant_area": plant_area,
        "description": text,
        "category": category,
        "severity": severity,
        "occurred_at": occurred_at,
        "duration": dur,
        "sensor_readings": readings,
        "temperature": temp,
        "operational_impact": impact,
        "safety_implications": None,
        "actions_taken": actions,
        "required_action": None,
        "reported_by": None,
        "inferred_fields": [],
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
            system = """You are an industrial incident extraction assistant. Extract structured fields from a worker's spoken report (may be Hindi/English/Hinglish/Tamil). Return ONLY valid JSON with keys:
machine_id (string or null), plant_area (string or null), description (string, factual summary only), category (one of: vibration, leak, overheating, noise, electrical, mechanical, safety, general), severity (critical|high|medium|low - only mark critical/high when worker states danger, injury, fire, smoke, shutdown, or production stoppage; otherwise medium/low), occurred_at (string or null), duration (string or null, e.g. "since yesterday"), sensor_readings (array of strings with units when stated), temperature (string or null with unit if explicitly stated), operational_impact (string or null, only if stated), safety_implications (string or null, only if stated), actions_taken (array of strings), required_action (string or null, only if worker requests), reported_by (string or null), inferred_fields (array of field names you inferred rather than explicitly stated), missing_fields (array of field names among: machine_id, plant_area, severity, occurred_at, sensor_readings, operational_impact), confidence (0-1 number reflecting extraction certainty, not a guess), questions (array of concise follow-up question strings, max 4, only for missing/ambiguous info). Do not invent details. If unknown use null. Distinguish stated facts from inferences."""
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
                "duration": data.get("duration"),
                "sensor_readings": data.get("sensor_readings") or [],
                "temperature": data.get("temperature"),
                "operational_impact": data.get("operational_impact"),
                "safety_implications": data.get("safety_implications"),
                "actions_taken": data.get("actions_taken") or [],
                "required_action": data.get("required_action"),
                "reported_by": data.get("reported_by"),
                "inferred_fields": data.get("inferred_fields") or [],
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
