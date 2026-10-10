"""Job CLI.

    python -m backend.jobs list                         # registered jobs
    python -m backend.jobs run hello --params '{"name": "x"}'
    python -m backend.jobs exec hello --run-id <id>     # job body (ECS task command)
    python -m backend.jobs runs [--job hello] [--status failed]
    python -m backend.jobs status <run-id>
    python -m backend.jobs pipelines
    python -m backend.jobs pipeline hello-pipeline [--overrides '{"greet-bob": {"name": "y"}}']
"""

import asyncio
import json
import sys
from typing import Any

import click

from backend.config import get_config


def _parse_json(value: str | None, option: str) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise click.BadParameter(f"invalid JSON: {exc}", param_hint=option) from None
    if not isinstance(parsed, dict):
        raise click.BadParameter("must be a JSON object", param_hint=option)
    return parsed


def _setup():
    from backend.database.db import SessionLocal, init_db
    from backend.jobs.registry import discover_jobs

    config = get_config()
    discover_jobs(config.job_modules)
    return config, SessionLocal, init_db


def _print_run(session_factory, run_id: str) -> str:
    from backend.repositories.job_run import JobRunRepository

    db = session_factory()
    try:
        repo = JobRunRepository(db)
        run = repo.get(run_id)
        if run is None:
            raise click.ClickException(f"run not found: {run_id}")
        payload = {
            "run_id": run.id,
            "kind": run.kind,
            "job": run.job_name,
            "status": run.status,
            "params": run.params,
            "result": run.result,
            "error": run.error,
            "external_id": run.external_id,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "artifacts": [a.uri for a in repo.list_artifacts(run.id)],
            "children": [
                {"run_id": c.id, "job": c.job_name, "status": c.status}
                for c in reversed(repo.list_runs(parent_run_id=run.id))
            ],
        }
        click.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return run.status
    finally:
        db.close()


@click.group()
def cli() -> None:
    """FDE job runner"""


@cli.command("list")
def list_cmd() -> None:
    """List registered jobs."""
    from backend.jobs.registry import list_jobs

    _setup()
    for name, cls in list_jobs().items():
        click.echo(f"{name}\t{cls.description}")


@cli.command("run")
@click.argument("job_name")
@click.option("--params", default=None, help="JSON object passed to the job")
@click.option("--wait/--no-wait", default=True, help="Wait for completion (ECS only)")
def run_cmd(job_name: str, params: str | None, wait: bool) -> None:
    """Launch a job through the configured launcher (JOB_LAUNCHER)."""
    from backend.factory import ServiceFactory
    from backend.jobs.registry import JobNotFoundError

    config, session_factory, init_db = _setup()
    init_db()
    launcher = ServiceFactory.create_job_launcher(config, session_factory)
    # A local CLI process must wait: its exit would orphan the supervisor.
    must_wait = wait or config.job_launcher == "local"
    try:
        run_id = asyncio.run(
            launcher.launch(job_name, _parse_json(params, "--params"), wait=must_wait)
        )
    except JobNotFoundError:
        raise click.ClickException(f"unknown job: {job_name}") from None
    status = _print_run(session_factory, run_id)
    sys.exit(1 if status == "failed" else 0)


@cli.command("exec")
@click.argument("job_name")
@click.option("--run-id", required=True)
def exec_cmd(job_name: str, run_id: str) -> None:
    """Execute a job body for an existing run (used by launchers / ECS)."""
    from backend.factory import ServiceFactory
    from backend.jobs.executor import execute_job

    config, session_factory, _ = _setup()
    store = ServiceFactory.create_object_store(config)
    sys.exit(execute_job(job_name, run_id, session_factory, store))


@cli.command("runs")
@click.option("--job", "job_name", default=None)
@click.option("--status", default=None)
@click.option("--limit", default=20, show_default=True)
def runs_cmd(job_name: str | None, status: str | None, limit: int) -> None:
    """List recent runs."""
    from backend.repositories.job_run import JobRunRepository

    _, session_factory, init_db = _setup()
    init_db()
    db = session_factory()
    try:
        for run in JobRunRepository(db).list_runs(job_name=job_name, status=status, limit=limit):
            click.echo(
                f"{run.created_at:%Y-%m-%d %H:%M:%S}\t{run.id}\t{run.kind}\t"
                f"{run.job_name}\t{run.status}"
            )
    finally:
        db.close()


@cli.command("status")
@click.argument("run_id")
def status_cmd(run_id: str) -> None:
    """Show one run with artifacts and child runs."""
    _, session_factory, _ = _setup()
    _print_run(session_factory, run_id)


@cli.command("pipelines")
def pipelines_cmd() -> None:
    """List pipeline definitions."""
    from backend.jobs.pipeline import load_pipelines

    config, _, _ = _setup()
    for name, pipeline in load_pipelines(config.job_pipelines_dir).items():
        steps = " -> ".join(s.id for s in pipeline.steps)
        click.echo(f"{name}\t{steps}\t{pipeline.description}")


@cli.command("pipeline")
@click.argument("pipeline_name")
@click.option("--overrides", default=None, help='JSON: {"<step id>": {params...}}')
def pipeline_cmd(pipeline_name: str, overrides: str | None) -> None:
    """Run a pipeline locally (AWS: Step Functions runs the same YAML)."""
    from backend.factory import ServiceFactory
    from backend.jobs.launcher import LocalJobLauncher
    from backend.jobs.pipeline import LocalPipelineRunner, PipelineDefinitionError, load_pipelines

    config, session_factory, init_db = _setup()
    pipeline = load_pipelines(config.job_pipelines_dir).get(pipeline_name)
    if pipeline is None:
        raise click.ClickException(f"unknown pipeline: {pipeline_name}")
    launcher = ServiceFactory.create_job_launcher(config, session_factory)
    if not isinstance(launcher, LocalJobLauncher):
        raise click.ClickException("pipelines run locally only; on AWS use Step Functions")
    init_db()
    runner = LocalPipelineRunner(launcher, session_factory)
    parsed = _parse_json(overrides, "--overrides")
    try:
        run_id = runner.create_run(pipeline, parsed)
    except PipelineDefinitionError as exc:
        raise click.ClickException(str(exc)) from None
    asyncio.run(runner.execute(pipeline, run_id, parsed))
    status = _print_run(session_factory, run_id)
    sys.exit(1 if status == "failed" else 0)


if __name__ == "__main__":
    cli()
