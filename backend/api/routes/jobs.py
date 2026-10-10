"""Job execution routes (adr/004-job-execution.md, docs/JOBS.md)"""

from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.database.models import JobRun
from backend.jobs.launcher import JobLauncher, spawn_background
from backend.jobs.pipeline import LocalPipelineRunner, PipelineDefinition, PipelineDefinitionError
from backend.jobs.registry import JobNotFoundError, list_jobs
from backend.repositories.job_run import ALL_STATUSES, JobRunRepository

router = APIRouter()
logger = structlog.get_logger()


class LaunchJobRequest(BaseModel):
    params: dict[str, Any] = {}


class LaunchPipelineRequest(BaseModel):
    overrides: dict[str, dict[str, Any]] = {}


def get_job_launcher() -> JobLauncher | None:
    from backend.api.main import get_job_launcher as _get

    return _get()


def get_pipeline_runner() -> LocalPipelineRunner | None:
    from backend.api.main import get_pipeline_runner as _get

    return _get()


def get_pipelines() -> dict[str, PipelineDefinition]:
    from backend.api.main import get_pipelines as _get

    return _get()


def _run_summary(run: JobRun) -> dict[str, Any]:
    return {
        "run_id": run.id,
        "kind": run.kind,
        "job_name": run.job_name,
        "parent_run_id": run.parent_run_id,
        "status": run.status,
        "launcher": run.launcher,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.get("/")
async def list_registered_jobs() -> dict[str, Any]:
    """Registered jobs"""
    jobs = [{"name": name, "description": cls.description} for name, cls in list_jobs().items()]
    return {"jobs": jobs}


@router.post("/{job_name}/runs", status_code=202)
async def launch_job(
    job_name: str,
    request: LaunchJobRequest,
    launcher: JobLauncher | None = Depends(get_job_launcher),
) -> dict[str, Any]:
    """Start a job asynchronously; poll GET /jobs/runs/{run_id}"""
    if launcher is None:
        raise HTTPException(status_code=503, detail="Job launcher not configured")
    try:
        run_id = await launcher.launch(job_name, request.params)
    except JobNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_name}")
    except Exception as e:
        logger.error("job_launch_error", job=job_name, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to launch job")
    return {"run_id": run_id, "job_name": job_name}


@router.get("/runs")
async def list_runs(
    job_name: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Recent runs, newest first"""
    if status and status not in ALL_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {sorted(ALL_STATUSES)}")
    runs = JobRunRepository(db).list_runs(job_name=job_name, status=status, limit=limit)
    return {"runs": [_run_summary(r) for r in runs]}


@router.get("/runs/{run_id}")
async def get_run(run_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Run detail with result, artifacts and child (pipeline step) runs"""
    repo = JobRunRepository(db)
    run = repo.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        **_run_summary(run),
        "params": run.params,
        "result": run.result,
        "error": run.error,
        "external_id": run.external_id,
        "artifacts": [
            {"name": a.name, "uri": a.uri, "metadata": a.artifact_metadata}
            for a in repo.list_artifacts(run.id)
        ],
        "children": [_run_summary(c) for c in reversed(repo.list_runs(parent_run_id=run.id))],
    }


@router.get("/pipelines")
async def list_pipelines(
    pipelines: dict[str, PipelineDefinition] = Depends(get_pipelines),
) -> dict[str, Any]:
    """Pipeline definitions"""
    return {
        "pipelines": [
            {
                "name": p.name,
                "description": p.description,
                "schedule": p.schedule,
                "steps": [{"id": s.id, "job": s.job} for s in p.steps],
            }
            for p in pipelines.values()
        ]
    }


@router.post("/pipelines/{pipeline_name}/runs", status_code=202)
async def launch_pipeline(
    pipeline_name: str,
    request: LaunchPipelineRequest,
    pipelines: dict[str, PipelineDefinition] = Depends(get_pipelines),
    runner: LocalPipelineRunner | None = Depends(get_pipeline_runner),
) -> dict[str, Any]:
    """Start a pipeline locally (on AWS, start the Step Functions state machine instead)"""
    if runner is None:
        raise HTTPException(
            status_code=501,
            detail="Pipelines run locally only (JOB_LAUNCHER=local); on AWS use Step Functions",
        )
    pipeline = pipelines.get(pipeline_name)
    if pipeline is None:
        raise HTTPException(status_code=404, detail=f"Unknown pipeline: {pipeline_name}")
    try:
        run_id = runner.create_run(pipeline, request.overrides)
    except PipelineDefinitionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    spawn_background(runner.execute(pipeline, run_id, request.overrides))
    return {"run_id": run_id, "pipeline": pipeline_name}
