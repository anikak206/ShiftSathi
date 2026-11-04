from sqlalchemy import create_engine, Column, String, Text, Float, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
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
    actions_taken = Column(Text, nullable=True)
    missing_info = Column(Text, nullable=True)
    recommended_next_steps = Column(Text, nullable=True)
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
