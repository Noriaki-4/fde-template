"""Sample job — copy this file to start a new job. Safe to delete."""

from typing import Any

from backend.jobs.base import Job
from backend.jobs.context import JobContext
from backend.jobs.registry import register_job


@register_job("hello")
class HelloJob(Job):
    description = "Sample job: greets, optionally writes an artifact or fails on purpose"

    async def run(self, ctx: JobContext) -> dict[str, Any]:
        name = str(ctx.params.get("name", "world"))
        if ctx.params.get("fail"):
            raise RuntimeError("failing on purpose (params.fail=true)")

        message = f"hello, {name}"
        ctx.logger.info("hello", message=message)

        output: dict[str, Any] = {"message": message}
        if ctx.params.get("write_artifact"):  # needs MinIO / S3
            output["artifact_uri"] = ctx.artifacts.put_json("greeting.json", {"message": message})
        return output
