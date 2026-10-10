"""LocalJobLauncher runs real `python -m backend.jobs exec` subprocesses on a sqlite file DB."""

import pytest

import backend.jobs.definitions.hello  # noqa: F401
from backend.jobs.launcher import LocalJobLauncher
from backend.jobs.registry import JobNotFoundError
from backend.repositories.job_run import JobRunRepository


def _get(session_factory, run_id):
    db = session_factory()
    try:
        return JobRunRepository(db).get(run_id)
    finally:
        db.close()


async def test_success(job_env, session_factory):
    run_id = await LocalJobLauncher(session_factory).launch("hello", {"name": "x"}, wait=True)
    run = _get(session_factory, run_id)
    assert run.status == "succeeded"
    assert run.result == {"message": "hello, x"}
    assert run.external_id.startswith("pid:")
    assert run.started_at and run.finished_at


async def test_job_exception_marks_failed(job_env, session_factory):
    run_id = await LocalJobLauncher(session_factory).launch("hello", {"fail": True}, wait=True)
    run = _get(session_factory, run_id)
    assert run.status == "failed"
    assert "failing on purpose" in run.error


async def test_hard_crash_still_recorded_as_failed(job_env, session_factory):
    """The job dies without writing anything; status comes from the process exit."""
    run_id = await LocalJobLauncher(session_factory).launch("test-crash", wait=True)
    run = _get(session_factory, run_id)
    assert run.status == "failed"
    assert run.error.startswith("exit code 3")
    assert run.result is None


async def test_timeout_kills_and_fails(job_env, session_factory):
    run_id = await LocalJobLauncher(session_factory).launch(
        "test-sleep", {"seconds": 30}, wait=True, timeout_seconds=1
    )
    run = _get(session_factory, run_id)
    assert run.status == "failed"
    assert "timed out" in run.error


async def test_unknown_job_records_nothing(job_env, session_factory):
    with pytest.raises(JobNotFoundError):
        await LocalJobLauncher(session_factory).launch("nope")
    db = session_factory()
    assert JobRunRepository(db).list_runs() == []


async def test_background_launch_completes(job_env, session_factory):
    import asyncio

    from backend.jobs import launcher as launcher_module

    run_id = await LocalJobLauncher(session_factory).launch("hello")
    await asyncio.gather(*launcher_module._background_tasks)
    assert _get(session_factory, run_id).status == "succeeded"


async def test_huge_stderr_line_does_not_leave_run_running(job_env, session_factory, capsys):
    run_id = await LocalJobLauncher(session_factory).launch("test-noisy", wait=True)
    run = _get(session_factory, run_id)
    assert run.status == "failed"
    assert "noisy failure" in run.error
