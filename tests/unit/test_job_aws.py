from datetime import datetime

import pytest

import backend.jobs.definitions.hello  # noqa: F401
from backend.config import Settings
from backend.factory import ServiceFactory
from backend.jobs.aws import EcsJobLauncher, ecs_event_to_run_event
from backend.jobs.launcher import LocalJobLauncher
from backend.repositories.job_run import JobRunRepository


def _event(status, exit_code=None, **detail):
    return {
        "detail-type": "ECS Task State Change",
        "source": "aws.ecs",
        "detail": {
            "startedBy": "run123",
            "taskArn": "arn:task/1",
            "lastStatus": status,
            "containers": [{"name": "job", "exitCode": exit_code}],
            **detail,
        },
    }


def test_running_event():
    ev = ecs_event_to_run_event(_event("RUNNING", startedAt="2026-10-10T01:02:03.000Z"), "job")
    assert ev.type == "started"
    assert ev.run_id == "run123"
    assert ev.external_id == "arn:task/1"
    assert ev.at == datetime(2026, 10, 10, 1, 2, 3)


def test_stopped_success():
    assert ecs_event_to_run_event(_event("STOPPED", 0), "job").type == "succeeded"


def test_stopped_failure_includes_reason():
    ev = ecs_event_to_run_event(
        _event("STOPPED", 137, stoppedReason="OutOfMemoryError: Container killed"), "job"
    )
    assert ev.type == "failed"
    assert "137" in ev.error and "OutOfMemory" in ev.error


def test_stopped_without_exit_code_is_failure():
    ev = ecs_event_to_run_event(
        _event("STOPPED", None, stoppedReason="Task failed to start"), "job"
    )
    assert ev.type == "failed"


@pytest.mark.parametrize(
    "event",
    [
        {"detail-type": "Something Else", "detail": {}},
        _event("PROVISIONING"),
        {"detail-type": "ECS Task State Change", "detail": {"lastStatus": "RUNNING"}},  # not ours
    ],
)
def test_irrelevant_events_ignored(event):
    assert ecs_event_to_run_event(event, "job") is None


class FakeEcs:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def run_task(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


def _launcher(session_factory, client):
    return EcsJobLauncher(
        session_factory,
        cluster="c",
        task_definition="td",
        container_name="job",
        subnets=["s1"],
        security_groups=["sg1"],
        ecs_client=client,
    )


async def test_ecs_launch_runs_task_with_exec_command(session_factory):
    client = FakeEcs({"tasks": [{"taskArn": "arn:task/9"}], "failures": []})
    run_id = await _launcher(session_factory, client).launch("hello", {"name": "x"})

    call = client.calls[0]
    assert call["startedBy"] == run_id
    assert call["overrides"]["containerOverrides"][0]["command"] == [
        "python",
        "-m",
        "backend.jobs",
        "exec",
        "hello",
        "--run-id",
        run_id,
    ]
    assert call["networkConfiguration"]["awsvpcConfiguration"]["securityGroups"] == ["sg1"]
    run = JobRunRepository(session_factory()).get(run_id)
    assert run.launcher == "ecs"
    assert run.status == "pending"  # RUNNING comes later via EventBridge
    assert run.external_id == "arn:task/9"


async def test_ecs_run_task_failure_marks_failed(session_factory):
    client = FakeEcs({"tasks": [], "failures": [{"reason": "RESOURCE:MEMORY"}]})
    run_id = await _launcher(session_factory, client).launch("hello")
    run = JobRunRepository(session_factory()).get(run_id)
    assert run.status == "failed"
    assert "RESOURCE:MEMORY" in run.error


def test_ecs_launcher_requires_config(session_factory):
    with pytest.raises(ValueError):
        EcsJobLauncher.from_config(Settings(job_launcher="ecs"), session_factory)


def test_factory_selects_launcher(session_factory):
    assert isinstance(
        ServiceFactory.create_job_launcher(Settings(job_launcher="local"), session_factory),
        LocalJobLauncher,
    )
    ecs = ServiceFactory.create_job_launcher(
        Settings(
            job_launcher="ecs", ecs_cluster="c", ecs_job_task_definition="td", ecs_subnets="a, b"
        ),
        session_factory,
    )
    assert isinstance(ecs, EcsJobLauncher)
    assert ecs._subnets == ["a", "b"]
    with pytest.raises(ValueError):
        ServiceFactory.create_job_launcher(Settings(job_launcher="k8s"), session_factory)


def test_lambda_handler_updates_run(monkeypatch, session_factory):
    import backend.database.db as db_module
    from backend.jobs import aws

    run = JobRunRepository(session_factory()).create("hello", {}, "ecs")
    monkeypatch.setattr(db_module, "SessionLocal", session_factory)
    event = _event("STOPPED", 0)
    event["detail"]["startedBy"] = run.id

    assert aws.lambda_handler(event, None) == {
        "handled": True,
        "run_id": run.id,
        "type": "succeeded",
    }
    assert JobRunRepository(session_factory()).get(run.id).status == "succeeded"
    assert aws.lambda_handler({"detail-type": "x"}, None) == {"handled": False}
