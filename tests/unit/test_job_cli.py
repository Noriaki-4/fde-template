import json

import pytest
from click.testing import CliRunner

import backend.database.db as db_module
from backend.jobs.__main__ import cli
from backend.repositories.job_run import JobRunRepository


@pytest.fixture
def cli_env(job_env, session_factory, monkeypatch):
    monkeypatch.setattr(db_module, "SessionLocal", session_factory)
    monkeypatch.setattr(db_module, "init_db", lambda: None)
    return CliRunner()


def _json(output):
    return json.loads(output[output.index("{") :])


def test_list(cli_env):
    result = cli_env.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "hello" in result.output


def test_run_success_and_status(cli_env):
    result = cli_env.invoke(cli, ["run", "hello", "--params", '{"name": "cli"}'])
    assert result.exit_code == 0, result.output
    payload = _json(result.output)
    assert payload["status"] == "succeeded"
    assert payload["result"] == {"message": "hello, cli"}

    status = cli_env.invoke(cli, ["status", payload["run_id"]])
    assert _json(status.output)["run_id"] == payload["run_id"]

    runs = cli_env.invoke(cli, ["runs", "--job", "hello"])
    assert payload["run_id"] in runs.output


def test_run_failure_exit_code(cli_env):
    result = cli_env.invoke(cli, ["run", "hello", "--params", '{"fail": true}'])
    assert result.exit_code == 1
    assert _json(result.output)["status"] == "failed"


@pytest.mark.parametrize("params", ["{bad", "[1]"])
def test_run_rejects_bad_params(cli_env, params):
    assert cli_env.invoke(cli, ["run", "hello", "--params", params]).exit_code == 2


def test_run_unknown_job(cli_env):
    result = cli_env.invoke(cli, ["run", "nope"])
    assert result.exit_code == 1
    assert "unknown job" in result.output


def test_status_unknown(cli_env):
    assert cli_env.invoke(cli, ["status", "missing"]).exit_code == 1


def test_exec_unknown_run_is_bad_request(cli_env):
    assert cli_env.invoke(cli, ["exec", "hello", "--run-id", "missing"]).exit_code == 2


def test_exec_job_name_mismatch(cli_env, session_factory):
    run = JobRunRepository(session_factory()).create("hello", {}, "local")
    assert cli_env.invoke(cli, ["exec", "test-sleep", "--run-id", run.id]).exit_code == 2


def test_pipelines_and_pipeline_run(cli_env):
    listed = cli_env.invoke(cli, ["pipelines"])
    assert "hello-pipeline" in listed.output

    result = cli_env.invoke(
        cli, ["pipeline", "hello-pipeline", "--overrides", '{"greet-bob": {"name": "robert"}}']
    )
    assert result.exit_code == 0, result.output
    payload = _json(result.output)
    assert payload["kind"] == "pipeline" and payload["status"] == "succeeded"
    assert [c["status"] for c in payload["children"]] == ["succeeded", "succeeded"]


def test_pipeline_unknown(cli_env):
    assert cli_env.invoke(cli, ["pipeline", "nope"]).exit_code == 1


def test_pipeline_bad_override(cli_env):
    result = cli_env.invoke(cli, ["pipeline", "hello-pipeline", "--overrides", '{"ghost": {}}'])
    assert result.exit_code == 1
    assert "unknown steps" in result.output
