import pytest

from backend.jobs.context import JobContext
from backend.repositories.job_run import JobRunRepository
from backend.storage.object_store import ObjectStore


class FakeStore(ObjectStore):
    def __init__(self):
        self.objects = {}

    def put_bytes(self, key, data, content_type="application/octet-stream"):
        uri = f"s3://bucket/{key}"
        self.objects[uri] = data
        return uri

    def get_bytes(self, uri):
        return self.objects[uri]


def _ctx(session_factory, store, run, parent_id=None):
    return JobContext.create(run.id, run.job_name, run.params, parent_id, store, session_factory)


def test_params_are_read_only(session_factory):
    db = session_factory()
    run = JobRunRepository(db).create("hello", {"a": 1}, "local")
    ctx = _ctx(session_factory, FakeStore(), run)
    with pytest.raises(TypeError):
        ctx.params["a"] = 2  # type: ignore[index]


def test_artifacts_written_under_run_prefix_and_recorded(session_factory):
    db = session_factory()
    repo = JobRunRepository(db)
    run = repo.create("hello", {}, "local")
    store = FakeStore()
    ctx = _ctx(session_factory, store, run)

    uri = ctx.artifacts.put_json("out/data.json", {"x": "日本語"})
    assert uri == f"s3://bucket/runs/{run.id}/hello/out/data.json"
    assert ctx.artifacts.get_json(uri) == {"x": "日本語"}
    assert [a.name for a in repo.list_artifacts(run.id)] == ["out/data.json"]


@pytest.mark.parametrize("name", ["", "/abs", "../escape", "a/../../b"])
def test_invalid_artifact_names(session_factory, name):
    db = session_factory()
    run = JobRunRepository(db).create("hello", {}, "local")
    ctx = _ctx(session_factory, FakeStore(), run)
    with pytest.raises(ValueError):
        ctx.artifacts.put_bytes(name, b"x")


def test_find_upstream_within_pipeline(session_factory):
    db = session_factory()
    repo = JobRunRepository(db)
    store = FakeStore()
    parent = repo.create("pipe", {}, "local", kind="pipeline")
    step1 = repo.create("extract", {}, "local", parent_run_id=parent.id)
    step2 = repo.create("load", {}, "local", parent_run_id=parent.id)

    uri = _ctx(session_factory, store, step1, parent.id).artifacts.put_json("rows.json", [1])
    assert uri.startswith(f"s3://bucket/runs/{parent.id}/extract/")

    step2_ctx = _ctx(session_factory, store, step2, parent.id)
    assert step2_ctx.artifacts.find_upstream("rows.json") == uri
    assert step2_ctx.artifacts.find_upstream("rows.json", job_name="other") is None
    assert step2_ctx.artifacts.find_upstream("missing.json") is None


def test_find_upstream_outside_pipeline_is_none(session_factory):
    db = session_factory()
    run = JobRunRepository(db).create("hello", {}, "local")
    assert _ctx(session_factory, FakeStore(), run).artifacts.find_upstream("x") is None
