import pytest

import backend.jobs.definitions.hello  # noqa: F401
from backend.api.main import app
from backend.api.routes import jobs as jobs_routes
from backend.jobs.pipeline import parse_pipeline
from backend.jobs.registry import get_job
from backend.repositories.job_run import JobRunRepository


class FakeLauncher:
    def __init__(self, db):
        self.db = db
        self.calls = []

    async def launch(self, job_name, params=None, **kwargs):
        get_job(job_name)
        self.calls.append((job_name, params))
        return JobRunRepository(self.db).create(job_name, params or {}, "fake").id


class FakeRunner:
    def __init__(self, db):
        self.db = db
        self.executed = []

    def create_run(self, pipeline, overrides=None):
        return JobRunRepository(self.db).create(pipeline.name, {}, "fake", kind="pipeline").id

    async def execute(self, pipeline, run_id, overrides=None):
        self.executed.append(run_id)
        return "succeeded"


PIPELINE = parse_pipeline({"name": "p", "steps": [{"id": "a", "job": "hello"}]})


@pytest.fixture
def overrides(db):
    launcher = FakeLauncher(db)
    runner = FakeRunner(db)
    app.dependency_overrides[jobs_routes.get_job_launcher] = lambda: launcher
    app.dependency_overrides[jobs_routes.get_pipeline_runner] = lambda: runner
    app.dependency_overrides[jobs_routes.get_pipelines] = lambda: {"p": PIPELINE}
    yield launcher, runner


def test_list_jobs(client, overrides):
    names = [j["name"] for j in client.get("/jobs/").json()["jobs"]]
    assert "hello" in names


def test_launch_and_get_run(client, overrides, db):
    launcher, _ = overrides
    response = client.post("/jobs/hello/runs", json={"params": {"name": "x"}})
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    assert launcher.calls == [("hello", {"name": "x"})]

    detail = client.get(f"/jobs/runs/{run_id}").json()
    assert detail["status"] == "pending"
    assert detail["params"] == {"name": "x"}
    assert detail["artifacts"] == [] and detail["children"] == []


def test_launch_unknown_job_404(client, overrides):
    assert client.post("/jobs/nope/runs", json={}).status_code == 404


def test_launch_without_launcher_503(client):
    app.dependency_overrides[jobs_routes.get_job_launcher] = lambda: None
    assert client.post("/jobs/hello/runs", json={}).status_code == 503


def test_list_runs_filters(client, overrides, db):
    repo = JobRunRepository(db)
    repo.create("hello", {}, "local")
    repo.create("other", {}, "local")
    runs = client.get("/jobs/runs", params={"job_name": "other"}).json()["runs"]
    assert [r["job_name"] for r in runs] == ["other"]
    assert client.get("/jobs/runs", params={"status": "bogus"}).status_code == 422


def test_get_run_404(client, overrides):
    assert client.get("/jobs/runs/missing").status_code == 404


def test_pipelines(client, overrides):
    _, runner = overrides
    listed = client.get("/jobs/pipelines").json()["pipelines"]
    assert listed[0]["name"] == "p" and listed[0]["steps"] == [{"id": "a", "job": "hello"}]

    response = client.post("/jobs/pipelines/p/runs", json={})
    assert response.status_code == 202
    assert client.post("/jobs/pipelines/ghost/runs", json={}).status_code == 404


def test_pipeline_without_local_runner_501(client, overrides):
    app.dependency_overrides[jobs_routes.get_pipeline_runner] = lambda: None
    assert client.post("/jobs/pipelines/p/runs", json={}).status_code == 501
