"""Executes one job body inside the job process / container.

This is what ``python -m backend.jobs exec <name> --run-id <id>`` runs — locally
as a subprocess, on AWS as the ECS task command. Params are read from the run
record, so the container command stays small and identical everywhere.
The exit code is the success signal; status itself is set from launcher events.
"""

import asyncio
import traceback

import structlog

from backend.jobs.context import JobContext, SessionFactory
from backend.jobs.registry import get_job
from backend.repositories.job_run import JobRunRepository
from backend.storage.object_store import ObjectStore

logger = structlog.get_logger()

EXIT_OK = 0
EXIT_JOB_FAILED = 1
EXIT_BAD_REQUEST = 2


def execute_job(
    job_name: str, run_id: str, session_factory: SessionFactory, store: ObjectStore
) -> int:
    db = session_factory()
    try:
        run = JobRunRepository(db).get(run_id)
        if run is None:
            logger.error("job_run_not_found", run_id=run_id)
            return EXIT_BAD_REQUEST
        if run.job_name != job_name:
            logger.error("job_name_mismatch", run_id=run_id, expected=run.job_name, got=job_name)
            return EXIT_BAD_REQUEST
        params = dict(run.params or {})
        parent_run_id = run.parent_run_id
    finally:
        db.close()

    ctx = JobContext.create(run_id, job_name, params, parent_run_id, store, session_factory)
    try:
        job = get_job(job_name)()
        result = asyncio.run(job.run(ctx))
    except Exception as exc:
        ctx.logger.error("job_failed", error=str(exc), traceback=traceback.format_exc())
        _save_result(session_factory, run_id, None, f"{type(exc).__name__}: {exc}")
        return EXIT_JOB_FAILED

    _save_result(session_factory, run_id, result, None)
    ctx.logger.info("job_succeeded")
    return EXIT_OK


def _save_result(
    session_factory: SessionFactory, run_id: str, result: dict | None, error: str | None
) -> None:
    db = session_factory()
    try:
        JobRunRepository(db).save_result(run_id, result, error)
    except Exception as exc:  # result is best-effort; status still comes from the exit code
        logger.error("job_result_save_failed", run_id=run_id, error=str(exc))
    finally:
        db.close()
