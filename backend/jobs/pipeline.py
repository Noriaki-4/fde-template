"""Pipeline definitions (YAML) and the local sequential runner.

One YAML step maps 1:1 to a Step Functions ``ecs:runTask.sync`` Task state on AWS
(timeout -> TimeoutSeconds, retries -> Retry, resources -> task cpu/memory), so the
same file drives local runs and the AWS state machine.
"""

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml

from backend.jobs.context import SessionFactory
from backend.jobs.events import STARTED, RunEvent, RunEventHandler
from backend.jobs.launcher import LocalJobLauncher
from backend.jobs.registry import JobNotFoundError, get_job
from backend.repositories.job_run import SUCCEEDED, JobRunRepository

DEFAULT_STEP_TIMEOUT_SECONDS = 3600


class PipelineDefinitionError(ValueError):
    pass


@dataclass(frozen=True)
class StepDefinition:
    id: str
    job: str
    params: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))
    timeout_seconds: int = DEFAULT_STEP_TIMEOUT_SECONDS
    retries: int = 0
    resources: Mapping[str, Any] = field(default_factory=lambda: MappingProxyType({}))


@dataclass(frozen=True)
class PipelineDefinition:
    name: str
    steps: tuple[StepDefinition, ...]
    description: str = ""
    schedule: str | None = None  # EventBridge Scheduler expression (AWS only)

    def validate_jobs(self) -> None:
        missing = []
        for step in self.steps:
            try:
                get_job(step.job)
            except JobNotFoundError:
                missing.append(step.job)
        if missing:
            raise PipelineDefinitionError(f"Pipeline {self.name!r}: unknown jobs {missing}")


def parse_pipeline(data: dict[str, Any], source: str = "<dict>") -> PipelineDefinition:
    if not isinstance(data, dict) or not data.get("name"):
        raise PipelineDefinitionError(f"{source}: 'name' is required")
    raw_steps = data.get("steps")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise PipelineDefinitionError(f"{source}: 'steps' must be a non-empty list")

    steps = []
    for index, raw in enumerate(raw_steps):
        if not isinstance(raw, dict) or not raw.get("job"):
            raise PipelineDefinitionError(f"{source}: step {index} needs 'job'")
        timeout = int(raw.get("timeout_seconds", DEFAULT_STEP_TIMEOUT_SECONDS))
        retries = int(raw.get("retries", 0))
        if timeout <= 0 or retries < 0:
            raise PipelineDefinitionError(f"{source}: step {index} has invalid timeout/retries")
        steps.append(
            StepDefinition(
                id=str(raw.get("id") or raw["job"]),
                job=str(raw["job"]),
                params=MappingProxyType(dict(raw.get("params") or {})),
                timeout_seconds=timeout,
                retries=retries,
                resources=MappingProxyType(dict(raw.get("resources") or {})),
            )
        )
    ids = [s.id for s in steps]
    if len(ids) != len(set(ids)):
        raise PipelineDefinitionError(f"{source}: step ids must be unique, got {ids}")

    return PipelineDefinition(
        name=str(data["name"]),
        steps=tuple(steps),
        description=str(data.get("description") or ""),
        schedule=data.get("schedule"),
    )


def load_pipelines(directory: str | Path) -> dict[str, PipelineDefinition]:
    path = Path(directory)
    if not path.is_dir():
        return {}
    pipelines: dict[str, PipelineDefinition] = {}
    for file in sorted([*path.glob("*.yaml"), *path.glob("*.yml")]):
        definition = parse_pipeline(yaml.safe_load(file.read_text()), str(file))
        if definition.name in pipelines:
            raise PipelineDefinitionError(f"Duplicate pipeline name {definition.name!r} in {file}")
        pipelines[definition.name] = definition
    return pipelines


class LocalPipelineRunner:
    """Runs steps sequentially through LocalJobLauncher (AWS uses Step Functions instead)."""

    def __init__(
        self,
        launcher: LocalJobLauncher,
        session_factory: SessionFactory,
        events: RunEventHandler | None = None,
    ):
        self._launcher = launcher
        self._session_factory = session_factory
        self._events = events or RunEventHandler(session_factory)

    def create_run(
        self, pipeline: PipelineDefinition, overrides: dict[str, dict[str, Any]] | None = None
    ) -> str:
        pipeline.validate_jobs()
        unknown = set(overrides or {}) - {s.id for s in pipeline.steps}
        if unknown:
            raise PipelineDefinitionError(f"Overrides for unknown steps: {sorted(unknown)}")
        db = self._session_factory()
        try:
            run = JobRunRepository(db).create(
                pipeline.name, {"overrides": overrides or {}}, "local", kind="pipeline"
            )
            return run.id
        finally:
            db.close()

    async def execute(
        self,
        pipeline: PipelineDefinition,
        run_id: str,
        overrides: dict[str, dict[str, Any]] | None = None,
    ) -> str:
        """Run all steps; returns the final pipeline status."""
        self._events.handle(RunEvent(run_id, STARTED))
        summary = []
        for step in pipeline.steps:
            params = {**step.params, **(overrides or {}).get(step.id, {})}
            child_id, status = await self._run_step(step, params, run_id)
            summary.append({"step": step.id, "job": step.job, "run_id": child_id, "status": status})
            if status != SUCCEEDED:
                self._save(run_id, {"steps": summary})
                self._events.handle(RunEvent(run_id, "failed", error=f"step {step.id!r} failed"))
                return "failed"
        self._save(run_id, {"steps": summary})
        self._events.handle(RunEvent(run_id, "succeeded"))
        return SUCCEEDED

    async def _run_step(
        self, step: StepDefinition, params: dict[str, Any], parent_run_id: str
    ) -> tuple[str, str]:
        child_id, status = "", "failed"
        for _attempt in range(step.retries + 1):
            child_id = await self._launcher.launch(
                step.job,
                params,
                parent_run_id=parent_run_id,
                wait=True,
                timeout_seconds=step.timeout_seconds,
            )
            status = self._status(child_id)
            if status == SUCCEEDED:
                break
        return child_id, status

    def _status(self, run_id: str) -> str:
        db = self._session_factory()
        try:
            run = JobRunRepository(db).get(run_id)
            return run.status if run else "failed"
        finally:
            db.close()

    def _save(self, run_id: str, result: dict[str, Any]) -> None:
        db = self._session_factory()
        try:
            JobRunRepository(db).save_result(run_id, result)
        finally:
            db.close()
