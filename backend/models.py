from sqlalchemy import (
    create_engine, Column, String, Integer, Float,
    DateTime, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum
import uuid

from config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ── Enums ──────────────────────────────────────────────────────────────────────

class Portal(str, enum.Enum):
    internshala = "internshala"
    linkedin = "linkedin"
    naukri = "naukri"


class AppStatus(str, enum.Enum):
    queued = "queued"
    in_progress = "in_progress"
    applied = "applied"
    failed = "failed"
    skipped = "skipped"


class RunStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"
    stopped = "stopped"


# ── Models ─────────────────────────────────────────────────────────────────────

class UserProfile(Base):
    __tablename__ = "user_profile"

    id = Column(Integer, primary_key=True, default=1)
    name = Column(String(100), default="")
    email = Column(String(200), default="")
    phone = Column(String(20), default="")

    # Job preferences
    target_roles = Column(Text, default="")       # comma-separated
    target_locations = Column(Text, default="")
    experience_level = Column(String(50), default="fresher")
    skills = Column(Text, default="")             # comma-separated
    min_stipend = Column(Integer, default=0)

    # Resume
    resume_filename = Column(String(300), default="")
    resume_text = Column(Text, default="")        # extracted text for LLM

    summary = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(SAEnum(RunStatus), default=RunStatus.running)
    portals = Column(Text, default="")            # comma-separated

    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    total_found = Column(Integer, default=0)
    total_applied = Column(Integer, default=0)
    total_failed = Column(Integer, default=0)

    applications = relationship("Application", back_populates="run")
    logs = relationship("AgentLog", back_populates="run", order_by="AgentLog.created_at")


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.id"))

    portal = Column(SAEnum(Portal))
    job_title = Column(String(300), default="")
    company = Column(String(200), default="")
    job_url = Column(Text, default="")
    job_description = Column(Text, default="")

    match_score = Column(Float, default=0.0)
    cover_letter = Column(Text, default="")
    resume_version = Column(String(100), default="default")

    status = Column(SAEnum(AppStatus), default=AppStatus.queued)
    error_message = Column(Text, default="")

    tinyfish_session_id = Column(String(200), default="")
    tinyfish_task_id = Column(String(200), default="")

    applied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("AgentRun", back_populates="applications")


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String(36), ForeignKey("agent_runs.id"))

    level = Column(String(10), default="info")    # info | success | warning | error
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("AgentRun", back_populates="logs")


# ── Helpers ────────────────────────────────────────────────────────────────────

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(UserProfile).first():
            db.add(UserProfile())
            db.commit()
    finally:
        db.close()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()