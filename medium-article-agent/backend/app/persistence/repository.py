"""Run persistence repository."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.persistence.db import DraftSnapshot, RunRecord, get_session_factory, init_db


class RunRepository:
    def __init__(self):
        init_db()
        self._session_factory = get_session_factory()

    def create_run(self, topic_hint: str = "") -> str:
        run_id = str(uuid.uuid4())
        with self._session_factory() as session:
            record = RunRecord(run_id=run_id, topic_hint=topic_hint, status="pending")
            session.add(record)
            session.commit()
        return run_id

    def update_run(self, run_id: str, status: str, state_snapshot: dict | None = None, export_path: str = ""):
        with self._session_factory() as session:
            record = session.get(RunRecord, run_id)
            if record:
                record.status = status
                record.updated_at = datetime.now(timezone.utc)
                if state_snapshot is not None:
                    record.state_snapshot = state_snapshot
                if export_path:
                    record.export_path = export_path
                session.commit()

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._session_factory() as session:
            return session.get(RunRecord, run_id)

    def list_by_status(self, status: str) -> list[str]:
        with self._session_factory() as session:
            rows = (
                session.query(RunRecord.run_id)
                .filter(RunRecord.status == status)
                .all()
            )
            return [row[0] for row in rows]

    def list_recent(self, limit: int = 5) -> list[dict]:
        with self._session_factory() as session:
            rows = (
                session.query(RunRecord)
                .order_by(RunRecord.updated_at.desc())
                .limit(limit)
                .all()
            )
            jobs = []
            for row in rows:
                snap = row.state_snapshot or {}
                plan = snap.get("plan") or {}
                title = ""
                if isinstance(plan, dict):
                    title = plan.get("title") or ""
                if not title:
                    md = snap.get("final_markdown") or snap.get("draft_markdown") or ""
                    if md.startswith("# "):
                        title = md.split("\n", 1)[0][2:].strip()
                jobs.append(
                    {
                        "run_id": row.run_id,
                        "status": row.status or "",
                        "topic_hint": row.topic_hint or "",
                        "title": title,
                        "iteration": snap.get("iteration", 0) or 0,
                        "open_findings_count": len(snap.get("open_findings") or []),
                        "updated_at": row.updated_at.isoformat() if row.updated_at else "",
                        "preview_url": f"/?run={row.run_id}",
                        "pipeline_url": f"/?run={row.run_id}&view=pipeline",
                    }
                )
            return jobs

    def save_draft_snapshot(self, run_id: str, iteration: int, markdown: str):
        snap_id = str(uuid.uuid4())[:12]
        with self._session_factory() as session:
            session.add(
                DraftSnapshot(
                    id=snap_id,
                    run_id=run_id,
                    iteration=str(iteration),
                    markdown=markdown,
                )
            )
            session.commit()

    def list_drafts(self, run_id: str) -> list[dict]:
        with self._session_factory() as session:
            rows = (
                session.query(DraftSnapshot)
                .filter(DraftSnapshot.run_id == run_id)
                .order_by(DraftSnapshot.created_at.asc())
                .all()
            )
            return [
                {
                    "id": row.id,
                    "iteration": row.iteration,
                    "markdown": row.markdown or "",
                    "created_at": row.created_at.isoformat() if row.created_at else "",
                }
                for row in rows
            ]
