import pytest
from app.services.llm import _extract_machine_id, _classify_category, _classify_severity, _extract_sensor_readings

def test_machine_id_code():
    assert _extract_machine_id("Pump P-12 has a leak") == "P-12"

def test_machine_id_bare():
    assert _extract_machine_id("Conveyor belt 7 temperature 95") == "7"

def test_machine_id_word():
    assert _extract_machine_id("Machine number five vibration") == "5"

def test_category_safety():
    assert _classify_category("Machine 9 electrical spark and smoke") == "safety"

def test_category_vibration():
    assert _classify_category("unusual vibration aa raha hai") == "vibration"

def test_severity_critical():
    assert _classify_severity("fire and smoke emergency") == "critical"

def test_severity_low():
    assert _classify_severity("minor issue routine check") == "low"
