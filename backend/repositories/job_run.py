"""Job run records (adr/004-job-execution.md).

Status transitions are applied only through ``apply_status`` which is called by
``RunEventHandler``; jobs themselves only save their result / artifacts.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.database.models import JobRun, RunArtifact

PENDING = "pending"
RUNNING = "running"
SUCCEEDED = "succeeded"
FAILED = "failed"
TERMINAL_STATUSES = frozenset({SUCCEEDED, FAILED})
ALL_STATUSES = frozenset({PENDING, RUNNING, SUCCEEDED, FAILED})


def new_run_id() -> str:
    return uuid.uuid4().hex


class JobRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        job_name: str,
        params: dict[str, Any],
        launcher: str,
        kind: str = "job",
        parent_run_id: str | None = None,
    ) -> JobRun:
        run = JobRun(
            id=new_run_id(),
            kind=kind,
            job_name=job_name,
            parent_run_id=parent_run_id,
            status=PENDING,
            params=dict(params),
            launcher=launcher,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get(self, run_id: str) -> JobRun | None:
        return self.db.query(JobRun).filter(JobRun.id == run_id).first()

    def list_runs(
        self,
        job_name: str | None = None,
        status: str | None = None,
        parent_run_id: str | None = None,
        limit: int = 50,
    ) -> list[JobRun]:
        query = self.db.query(JobRun)
        if job_name:
            query = query.filter(JobRun.job_name == job_name)
        if status:
            query = query.filter(JobRun.status == status)
        if parent_run_id:
            query = query.filter(JobRun.parent_run_id == parent_run_id)
        return query.order_by(JobRun.created_at.desc()).limit(limit).all()

    def apply_status(
        self,
        run_id: str,
        status: str,
        at: datetime,
        external_id: str | None = None,
        error: str | None = None,
    ) -> JobRun | None:
        """Apply a status transition. Idempotent; terminal runs are never changed."""
        if status not in ALL_STATUSES:
            raise ValueError(f"Unknown run status: {status}")
        run = self.get(run_id)
        if run is None or run.status in TERMINAL_STATUSES:
            return run
        if status == RUNNING and run.status == RUNNING:
            return run
        run.status = status
        if external_id:
            run.external_id = external_id
        if status == RUNNING:
            run.started_at = at
        if status in TERMINAL_STATUSES:
            run.started_at = run.started_at or at
            run.finished_at = at
        if error:
            # keep the job's own error message (saved by the executor) and append ours
            run.error = f"{run.error}\n[{error}]" if run.error else error
        self.db.commit()
        self.db.refresh(run)
        return run

    def set_external_id(self, run_id: str, external_id: str) -> None:
        run = self.get(run_id)
        if run is not None:
            run.external_id = external_id
            self.db.commit()

    def save_result(
        self, run_id: str, result: dict[str, Any] | None, error: str | None = None
    ) -> None:
        """Save the job's own output (data, not status)."""
        run = self.get(run_id)
        if run is None:
            raise ValueError(f"Run not found: {run_id}")
        run.result = result
        if error:
            run.error = error
        self.db.commit()

    def add_artifact(
        self, run_id: str, name: str, uri: str, metadata: dict[str, Any] | None = None
    ) -> RunArtifact:
        artifact = RunArtifact(run_id=run_id, name=name, uri=uri, artifact_metadata=metadata)
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def list_artifacts(self, run_id: str) -> list[RunArtifact]:
        return (
            self.db.query(RunArtifact)
            .filter(RunArtifact.run_id == run_id)
            .order_by(RunArtifact.id)
            .all()
        )
