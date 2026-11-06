import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_extract_hinglish():
    r = client.post("/api/extract", json={"transcript": "Machine number five mein unusual vibration aa raha hai."})
    assert r.status_code == 200
    data = r.json()
    assert data["fields"]["machine_id"] == "5"
    assert data["fields"]["category"] == "vibration"
    assert "machine_id" not in data["missing_fields"]

def test_extract_critical():
    r = client.post("/api/extract", json={"transcript": "Machine 9 electrical spark and smoke, emergency shutdown done."})
    assert r.status_code == 200
    data = r.json()
    assert data["fields"]["severity"] == "critical"

def test_session_flow():
    r = client.post("/api/sessions/start", json={"transcript": "Pump P-12 in production area line 2 has oil leak, machine stopped, critical."})
    assert r.status_code == 200
    sid = r.json()["id"]
    r2 = client.post(f"/api/sessions/{sid}/confirm", json={"edited_fields": {}})
    assert r2.status_code == 200
    assert r2.json()["machine_id"] == "P-12"

def test_dashboard():
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    assert "total" in r.json()

def test_eval_run():
    r = client.post("/api/eval/run")
    assert r.status_code == 200
    assert r.json()["summary"]["samples"] == 50
