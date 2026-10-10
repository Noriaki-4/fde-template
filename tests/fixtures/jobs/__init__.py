"""Jobs used only by tests (loaded via JOB_MODULES=...,tests.fixtures.jobs)."""

import asyncio
import os
from typing import Any

from backend.jobs.base import Job
from backend.jobs.context import JobContext
from backend.jobs.registry import register_job


@register_job("test-sleep")
class SleepJob(Job):
    description = "sleeps params.seconds"

    async def run(self, ctx: JobContext) -> dict[str, Any]:
        await asyncio.sleep(float(ctx.params.get("seconds", 0)))
        return {"slept": ctx.params.get("seconds", 0)}


@register_job("test-crash")
class CrashJob(Job):
    description = "hard-exits without reporting anything (simulates OOM kill)"

    async def run(self, ctx: JobContext) -> dict[str, Any]:
        os._exit(3)


@register_job("test-flaky")
class FlakyJob(Job):
    """Fails until a marker file exists, then succeeds (for retry tests)."""

    description = "fails on first attempt"

    async def run(self, ctx: JobContext) -> dict[str, Any]:
        marker = str(ctx.params["marker"])
        if not os.path.exists(marker):
            open(marker, "w").close()
            raise RuntimeError("first attempt fails")
        return {"ok": True}


@register_job("test-noisy")
class NoisyJob(Job):
    """Writes one huge stderr line (> asyncio's 64 KiB readline limit), then fails."""

    description = "huge stderr line"

    async def run(self, ctx: JobContext) -> dict[str, Any]:
        import sys

        sys.stderr.write("x" * 200_000 + "\n")
        sys.stderr.flush()
        raise RuntimeError("noisy failure")
