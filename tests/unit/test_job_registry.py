import pytest

from backend.jobs.base import Job
from backend.jobs.registry import (
    JobNotFoundError,
    discover_jobs,
    get_job,
    list_jobs,
    register_job,
)


def test_discover_registers_sample_job():
    discover_jobs("backend.jobs.definitions")
    assert get_job("hello").name == "hello"
    assert "hello" in list_jobs()


def test_unknown_job_raises():
    with pytest.raises(JobNotFoundError):
        get_job("does-not-exist")


def test_invalid_name_rejected():
    with pytest.raises(ValueError):

        @register_job("bad name!")
        class _Bad(Job):
            async def run(self, ctx):
                return {}


def test_duplicate_name_from_other_class_rejected():
    discover_jobs("backend.jobs.definitions")
    with pytest.raises(ValueError, match="already registered"):

        @register_job("hello")
        class _Other(Job):
            async def run(self, ctx):
                return {}
