"""Run lifecycle events and the single place that turns them into run status.

Local: LocalJobLauncher emits events when the subprocess starts / exits.
AWS:   EventBridge (ECS Task State Change) -> Lambda -> backend.jobs.aws.lambda_handler.
Both call ``RunEventHandler.handle`` so status logic is identical.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

import structlog

from backend.jobs.context import SessionFactory
from backend.repositories.job_run import FAILED, RUNNING, SUCCEEDED, JobRunRepository

logger = structlog.get_logger()

STARTED = "started"
EVENT_TO_STATUS = {STARTED: RUNNING, "succeeded": SUCCEEDED, "failed": FAILED}


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True)
class RunEvent:
    run_id: str
    type: str  # started | succeeded | failed
    at: datetime = field(default_factory=utcnow)
    external_id: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.type not in EVENT_TO_STATUS:
            raise ValueError(f"Unknown run event type: {self.type}")


class RunEventHandler:
    def __init__(self, session_factory: SessionFactory):
        self._session_factory = session_factory

    def handle(self, event: RunEvent) -> None:
        db = self._session_factory()
        try:
            run = JobRunRepository(db).apply_status(
                event.run_id,
                EVENT_TO_STATUS[event.type],
                event.at,
                external_id=event.external_id,
                error=event.error,
            )
            if run is None:
                logger.warning("run_event_unknown_run", run_id=event.run_id, type=event.type)
            else:
                logger.info("run_event", run_id=event.run_id, type=event.type, status=run.status)
        finally:
            db.close()
