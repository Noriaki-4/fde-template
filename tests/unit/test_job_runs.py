from datetime import datetime

import pytest

from backend.jobs.events import RunEvent, RunEventHandler
from backend.repositories.job_run import JobRunRepository


@pytest.fixture
def repo(session_factory):
    db = session_factory()
    yield JobRunRepository(db)
    db.close()


def _status(session_factory, run_id):
    db = session_factory()
    try:
        return JobRunRepository(db).get(run_id)
    finally:
        db.close()


def test_create_is_pending(repo):
    run = repo.create("hello", {"a": 1}, "local")
    assert run.status == "pending"
    assert run.params == {"a": 1}
    assert len(run.id) == 32


def test_event_lifecycle(session_factory, repo):
    run = repo.create("hello", {}, "local")
    handler = RunEventHandler(session_factory)

    handler.handle(RunEvent(run.id, "started", external_id="pid:1"))
    current = _status(session_factory, run.id)
    assert current.status == "running"
    assert current.external_id == "pid:1"
    assert current.started_at is not None

    handler.handle(RunEvent(run.id, "succeeded"))
    current = _status(session_factory, run.id)
    assert current.status == "succeeded"
    assert current.finished_at is not None


def test_terminal_status_is_final(session_factory, repo):
    run = repo.create("hello", {}, "local")
    handler = RunEventHandler(session_factory)
    handler.handle(RunEvent(run.id, "failed", error="boom"))
    handler.handle(RunEvent(run.id, "succeeded"))  # late / duplicate event
    current = _status(session_factory, run.id)
    assert current.status == "failed"
    assert current.error == "boom"


def test_stopped_without_started_event(session_factory, repo):
    """Out-of-order delivery: terminal event arrives first."""
    run = repo.create("hello", {}, "ecs")
    RunEventHandler(session_factory).handle(RunEvent(run.id, "succeeded"))
    current = _status(session_factory, run.id)
    assert current.status == "succeeded"
    assert current.started_at is not None


def test_unknown_run_event_is_ignored(session_factory):
    RunEventHandler(session_factory).handle(RunEvent("nope", "started"))


def test_invalid_event_type():
    with pytest.raises(ValueError):
        RunEvent("x", "exploded")


def test_invalid_status_rejected(repo):
    run = repo.create("hello", {}, "local")
    with pytest.raises(ValueError):
        repo.apply_status(run.id, "weird", datetime.utcnow())


def test_list_filters_and_children(repo):
    parent = repo.create("p", {}, "local", kind="pipeline")
    child = repo.create("hello", {}, "local", parent_run_id=parent.id)
    repo.create("other", {}, "local")
    assert [r.id for r in repo.list_runs(parent_run_id=parent.id)] == [child.id]
    assert {r.job_name for r in repo.list_runs(job_name="other")} == {"other"}
    assert repo.list_runs(status="succeeded") == []


def test_result_and_artifacts(repo):
    run = repo.create("hello", {}, "local")
    repo.save_result(run.id, {"n": 1})
    repo.add_artifact(run.id, "a.json", "s3://b/a.json", {"size": 2})
    assert repo.get(run.id).result == {"n": 1}
    assert [a.uri for a in repo.list_artifacts(run.id)] == ["s3://b/a.json"]
    with pytest.raises(ValueError):
        repo.save_result("missing", {})
