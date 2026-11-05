import os
from pathlib import Path
from sqlalchemy import create_engine, Column, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from .config import DATABASE_URL, BASE_DIR

_db_url = DATABASE_URL
if _db_url.startswith("sqlite:///") and not _db_url.startswith("sqlite:////"):
    rel = _db_url.replace("sqlite:///", "")
    if not os.path.isabs(rel):
        _db_url = "sqlite:///" + (BASE_DIR / rel).as_posix()

engine = create_engine(_db_url, connect_args={"check_same_thread": False} if _db_url.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)
    machine_id = Column(String, nullable=True)
    plant_area = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True)
    severity = Column(String, nullable=True)
    occurred_at = Column(String, nullable=True)
    sensor_readings = Column(Text, nullable=True)
    temperature = Column(String, nullable=True)
    duration = Column(String, nullable=True)
    operational_impact = Column(Text, nullable=True)
    safety_implications = Column(Text, nullable=True)
    actions_taken = Column(Text, nullable=True)
    required_action = Column(Text, nullable=True)
    reported_by = Column(String, nullable=True)
    inferred_fields = Column(Text, nullable=True)
    missing_info = Column(Text, nullable=True)
    recommended_next_steps = Column(Text, nullable=True)
    corrections = Column(Text, nullable=True)
    status = Column(String, default="open")
    confirmation_status = Column(String, default="confirmed")
    transcript = Column(Text, nullable=True)
    confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ensure tables exist even when startup event is not triggered (e.g., tests)
try:
    init_db()
except Exception:
    pass
