import pytest

import backend.jobs.definitions.hello  # noqa: F401
from backend.jobs.launcher import LocalJobLauncher
from backend.jobs.pipeline import (
    LocalPipelineRunner,
    PipelineDefinitionError,
    load_pipelines,
    parse_pipeline,
)
from backend.repositories.job_run import JobRunRepository


def test_parse_defaults():
    p = parse_pipeline({"name": "p", "steps": [{"job": "hello"}]})
    assert p.steps[0].id == "hello"
    assert p.steps[0].timeout_seconds == 3600
    assert p.steps[0].retries == 0
    assert p.schedule is None


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"name": "p"},
        {"name": "p", "steps": []},
        {"name": "p", "steps": [{"params": {}}]},
        {"name": "p", "steps": [{"job": "a"}, {"job": "a"}]},
        {"name": "p", "steps": [{"job": "a", "retries": -1}]},
        {"name": "p", "steps": [{"job": "a", "timeout_seconds": 0}]},
    ],
)
def test_parse_rejects_invalid(data):
    with pytest.raises(PipelineDefinitionError):
        parse_pipeline(data)


def test_bundled_sample_pipeline_is_valid():
    pipelines = load_pipelines("backend/jobs/pipelines")
    assert "hello-pipeline" in pipelines
    pipelines["hello-pipeline"].validate_jobs()


def test_load_missing_dir_is_empty(tmp_path):
    assert load_pipelines(tmp_path / "none") == {}


def test_duplicate_names_rejected(tmp_path):
    for f in ("a.yaml", "b.yaml"):
        (tmp_path / f).write_text("name: same\nsteps: [{job: hello}]\n")
    with pytest.raises(PipelineDefinitionError):
        load_pipelines(tmp_path)


def _runner(session_factory):
    return LocalPipelineRunner(LocalJobLauncher(session_factory), session_factory)


def test_unknown_job_rejected_before_run(session_factory):
    p = parse_pipeline({"name": "p", "steps": [{"job": "nope"}]})
    with pytest.raises(PipelineDefinitionError):
        _runner(session_factory).create_run(p)


def test_unknown_override_step_rejected(session_factory):
    p = parse_pipeline({"name": "p", "steps": [{"job": "hello"}]})
    with pytest.raises(PipelineDefinitionError):
        _runner(session_factory).create_run(p, {"ghost": {}})


async def test_runs_steps_in_order_with_overrides(job_env, session_factory):
    p = parse_pipeline(
        {
            "name": "p",
            "steps": [
                {"id": "a", "job": "hello", "params": {"name": "a"}},
                {"id": "b", "job": "hello", "params": {"name": "b"}},
            ],
        }
    )
    runner = _runner(session_factory)
    overrides = {"b": {"name": "B"}}
    run_id = runner.create_run(p, overrides)
    assert await runner.execute(p, run_id, overrides) == "succeeded"

    repo = JobRunRepository(session_factory())
    parent = repo.get(run_id)
    assert parent.kind == "pipeline" and parent.status == "succeeded"
    children = list(reversed(repo.list_runs(parent_run_id=run_id)))
    assert [c.result["message"] for c in children] == ["hello, a", "hello, B"]


async def test_failed_step_stops_pipeline(job_env, session_factory):
    p = parse_pipeline(
        {
            "name": "p",
            "steps": [
                {"id": "bad", "job": "hello", "params": {"fail": True}},
                {"id": "never", "job": "hello"},
            ],
        }
    )
    runner = _runner(session_factory)
    run_id = runner.create_run(p)
    assert await runner.execute(p, run_id) == "failed"

    repo = JobRunRepository(session_factory())
    parent = repo.get(run_id)
    assert parent.status == "failed"
    assert "bad" in parent.error
    assert [s["step"] for s in parent.result["steps"]] == ["bad"]


async def test_retries(job_env, session_factory, tmp_path):
    marker = tmp_path / "marker"
    p = parse_pipeline(
        {
            "name": "p",
            "steps": [{"job": "test-flaky", "retries": 1, "params": {"marker": str(marker)}}],
        }
    )
    runner = _runner(session_factory)
    run_id = runner.create_run(p)
    assert await runner.execute(p, run_id) == "succeeded"
    children = JobRunRepository(session_factory()).list_runs(parent_run_id=run_id)
    assert sorted(c.status for c in children) == ["failed", "succeeded"]
