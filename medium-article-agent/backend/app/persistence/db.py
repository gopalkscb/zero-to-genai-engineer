"""SQLAlchemy database setup."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class RunRecord(Base):
    __tablename__ = "runs"

    run_id = Column(String, primary_key=True)
    status = Column(String, default="pending")
    topic_hint = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    state_snapshot = Column(JSON, default=dict)
    export_path = Column(String, default="")


class DraftSnapshot(Base):
    __tablename__ = "draft_snapshots"

    id = Column(String, primary_key=True)
    run_id = Column(String, index=True)
    iteration = Column(String, default="0")
    markdown = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url
        if db_url.startswith("sqlite:///./"):
            db_path = settings.data_dir / "medium_agent.db"
            db_url = f"sqlite:///{db_path}"
        _engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def init_db():
    Base.metadata.create_all(get_engine())
