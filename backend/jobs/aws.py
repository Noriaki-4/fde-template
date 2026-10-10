"""AWS side of the job framework.

- ``EcsJobLauncher`` starts a run as an ECS Fargate task (``startedBy`` = run id).
- ``ecs_event_to_run_event`` / ``lambda_handler`` turn EventBridge
  "ECS Task State Change" events into ``RunEvent``s handled by the same
  ``RunEventHandler`` the local launcher uses.

Pipelines on AWS are Step Functions state machines generated from the same
pipeline YAML (see docs/JOBS.md); they are not driven from this module.
"""

import asyncio
from datetime import datetime
from typing import Any

import structlog

from backend.config import Settings
from backend.jobs.context import SessionFactory
from backend.jobs.events import STARTED, RunEvent, RunEventHandler
from backend.jobs.launcher import JobLauncher, job_command
from backend.repositories.job_run import JobRunRepository

logger = structlog.get_logger()

ECS_TASK_STATE_CHANGE = "ECS Task State Change"


def _split(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


class EcsJobLauncher(JobLauncher):
    name = "ecs"

    def __init__(
        self,
        session_factory: SessionFactory,
        cluster: str,
        task_definition: str,
        container_name: str,
        subnets: list[str],
        security_groups: list[str],
        ecs_client: Any = None,
        events: RunEventHandler | None = None,
    ):
        super().__init__(session_factory, events)
        if not cluster or not task_definition or not subnets:
            raise ValueError(
                "ECS launcher requires ecs_cluster, ecs_job_task_definition, ecs_subnets"
            )
        self._cluster = cluster
        self._task_definition = task_definition
        self._container_name = container_name
        self._subnets = subnets
        self._security_groups = security_groups
        self._client = ecs_client

    @classmethod
    def from_config(cls, config: Settings, session_factory: SessionFactory) -> "EcsJobLauncher":
        return cls(
            session_factory,
            cluster=config.ecs_cluster,
            task_definition=config.ecs_job_task_definition,
            container_name=config.ecs_job_container_name,
            subnets=_split(config.ecs_subnets),
            security_groups=_split(config.ecs_security_groups),
        )

    @property
    def client(self):
        if self._client is None:
            import boto3

            self._client = boto3.client("ecs")
        return self._client

    async def _start(
        self, job_name: str, run_id: str, *, wait: bool, timeout_seconds: int | None
    ) -> None:
        # timeout_seconds is enforced by Step Functions (TimeoutSeconds) on AWS
        response = await asyncio.to_thread(self._run_task, job_name, run_id)
        tasks = response.get("tasks") or []
        if not tasks:
            reason = "; ".join(f.get("reason", "unknown") for f in response.get("failures", []))
            # No task => no ECS state-change event will ever arrive; fail now.
            self._events.handle(RunEvent(run_id, "failed", error=f"run_task failed: {reason}"))
            return
        task_arn = tasks[0]["taskArn"]
        db = self._session_factory()
        try:
            JobRunRepository(db).set_external_id(run_id, task_arn)
        finally:
            db.close()
        if wait:
            waiter = self.client.get_waiter("tasks_stopped")
            await asyncio.to_thread(waiter.wait, cluster=self._cluster, tasks=[task_arn])

    def _run_task(self, job_name: str, run_id: str) -> dict[str, Any]:
        network = {"subnets": self._subnets, "assignPublicIp": "DISABLED"}
        if self._security_groups:
            network["securityGroups"] = self._security_groups
        return self.client.run_task(
            cluster=self._cluster,
            taskDefinition=self._task_definition,
            launchType="FARGATE",
            startedBy=run_id,
            networkConfiguration={"awsvpcConfiguration": network},
            overrides={
                "containerOverrides": [
                    {"name": self._container_name, "command": job_command(job_name, run_id)}
                ]
            },
        )


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def ecs_event_to_run_event(event: dict[str, Any], container_name: str) -> RunEvent | None:
    """Translate an EventBridge ECS Task State Change event. Returns None if irrelevant."""
    if event.get("detail-type") != ECS_TASK_STATE_CHANGE:
        return None
    detail = event.get("detail") or {}
    run_id = detail.get("startedBy")
    if not run_id:
        return None
    task_arn = detail.get("taskArn")
    status = detail.get("lastStatus")

    if status == "RUNNING":
        at = _parse_time(detail.get("startedAt"))
        return RunEvent(run_id, STARTED, external_id=task_arn, **({"at": at} if at else {}))
    if status != "STOPPED":
        return None

    at = _parse_time(detail.get("stoppedAt"))
    container = next(
        (c for c in detail.get("containers", []) if c.get("name") == container_name), {}
    )
    exit_code = container.get("exitCode")
    extra = {"at": at} if at else {}
    if exit_code == 0:
        return RunEvent(run_id, "succeeded", external_id=task_arn, **extra)
    reason = container.get("reason") or detail.get("stoppedReason") or "unknown"
    return RunEvent(
        run_id, "failed", external_id=task_arn, error=f"exit code {exit_code}: {reason}", **extra
    )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """EventBridge rule (source=aws.ecs, detail-type=ECS Task State Change) target."""
    from backend.config import get_config
    from backend.database.db import SessionLocal

    run_event = ecs_event_to_run_event(event, get_config().ecs_job_container_name)
    if run_event is None:
        return {"handled": False}
    RunEventHandler(SessionLocal).handle(run_event)
    return {"handled": True, "run_id": run_event.run_id, "type": run_event.type}
