import json, os
from fastapi import APIRouter
from ..services.llm import extract as llm_extract

router = APIRouter(prefix="/api/eval", tags=["eval"])

@router.get("/dataset")
def dataset():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval_dataset.json")
    with open(os.path.abspath(path)) as f:
        return json.load(f)

@router.post("/run")
async def run_eval():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "eval_dataset.json")
    with open(os.path.abspath(path)) as f:
        data = json.load(f)
    results = []
    field_correct = 0; total_fields = 0
    missing_detected = 0
    for item in data:
        r = await llm_extract(item["transcript"])
        f = r["fields"]
        exp = item["expected"]
        # field accuracy for machine_id, category, severity
        for key in ["machine_id","category","severity"]:
            total_fields += 1
            got = str(f.get(key)).lower() if f.get(key) is not None else ""
            expv = str(exp.get(key)).lower()
            if got == expv:
                field_correct += 1
        results.append({
            "id": item["id"],
            "transcript": item["transcript"],
            "extracted": f,
            "expected": exp,
            "confidence": r["confidence"],
            "missing_fields": r["missing_fields"],
            "questions": r["questions"],
            "source": r.get("source"),
        })
    return {
        "summary": {
            "samples": len(data),
            "field_accuracy": round(field_correct/total_fields, 3) if total_fields else 0,
            "fields_checked": total_fields,
            "fields_correct": field_correct,
        },
        "results": results,
    }
