"""Job launchers: create the run record, start the job process, report lifecycle events.

``LocalJobLauncher`` runs ``python -m backend.jobs exec`` as a subprocess (the same
command ECS runs on AWS) and emits started / succeeded / failed events from the
process lifecycle, so even a crashed or killed job is recorded as failed.
"""

import asyncio
import collections
import sys
from abc import ABC, abstractmethod
from typing import Any

import structlog

from backend.jobs.context import SessionFactory
from backend.jobs.events import STARTED, RunEvent, RunEventHandler
from backend.jobs.registry import get_job
from backend.repositories.job_run import JobRunRepository

logger = structlog.get_logger()

STDERR_TAIL_LINES = 20

# Strong references to fire-and-forget supervisors (asyncio only keeps weak refs)
_background_tasks: set[asyncio.Task] = set()


def job_command(job_name: str, run_id: str) -> list[str]:
    """Container / process command for one job run (shared by local and ECS)."""
    return ["python", "-m", "backend.jobs", "exec", job_name, "--run-id", run_id]


def spawn_background(coro) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


class JobLauncher(ABC):
    name: str = ""

    def __init__(self, session_factory: SessionFactory, events: RunEventHandler | None = None):
        self._session_factory = session_factory
        self._events = events or RunEventHandler(session_factory)

    async def launch(
        self,
        job_name: str,
        params: dict[str, Any] | None = None,
        *,
        parent_run_id: str | None = None,
        wait: bool = False,
        timeout_seconds: int | None = None,
    ) -> str:
        """Create a run record and start it. Returns the run id.

        Raises JobNotFoundError for unknown jobs before anything is recorded.
        """
        get_job(job_name)
        db = self._session_factory()
        try:
            run = JobRunRepository(db).create(
                job_name, params or {}, self.name, parent_run_id=parent_run_id
            )
            run_id = run.id
        finally:
            db.close()
        await self._start(job_name, run_id, wait=wait, timeout_seconds=timeout_seconds)
        return run_id

    @abstractmethod
    async def _start(
        self, job_name: str, run_id: str, *, wait: bool, timeout_seconds: int | None
    ) -> None: ...


class LocalJobLauncher(JobLauncher):
    name = "local"

    async def _start(
        self, job_name: str, run_id: str, *, wait: bool, timeout_seconds: int | None
    ) -> None:
        supervisor = self._supervise(job_name, run_id, timeout_seconds)
        if wait:
            await supervisor
        else:
            spawn_background(supervisor)

    async def _supervise(self, job_name: str, run_id: str, timeout_seconds: int | None) -> None:
        command = [sys.executable, *job_command(job_name, run_id)[1:]]
        try:
            proc = await asyncio.create_subprocess_exec(*command, stderr=asyncio.subprocess.PIPE)
        except OSError as exc:
            self._events.handle(RunEvent(run_id, "failed", error=f"spawn failed: {exc}"))
            return

        self._events.handle(RunEvent(run_id, STARTED, external_id=f"pid:{proc.pid}"))
        try:
            event = await self._wait(proc, run_id, timeout_seconds)
        except Exception as exc:  # never leave a run stuck in "running"
            if proc.returncode is None:
                proc.kill()
            event = RunEvent(run_id, "failed", error=f"supervisor error: {exc}")
        self._events.handle(event)

    async def _wait(
        self, proc: asyncio.subprocess.Process, run_id: str, timeout_seconds: int | None
    ) -> RunEvent:
        tail: collections.deque[str] = collections.deque(maxlen=STDERR_TAIL_LINES)
        drain = asyncio.create_task(_forward_stderr(proc.stderr, tail))
        try:
            returncode = await asyncio.wait_for(proc.wait(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            await drain
            return RunEvent(run_id, "failed", error=f"timed out after {timeout_seconds}s")
        await drain

        if returncode == 0:
            return RunEvent(run_id, "succeeded")
        detail = "".join(tail).strip()
        return RunEvent(run_id, "failed", error=f"exit code {returncode}\n{detail}".strip())


async def _forward_stderr(stream: asyncio.StreamReader | None, tail: collections.deque) -> None:
    """Forward child stderr in chunks (no line-length limit) and keep the last lines."""
    if stream is None:
        return
    while chunk := await stream.read(4096):
        text = chunk.decode("utf-8", errors="replace")
        sys.stderr.write(text)
        tail.extend(text.splitlines(keepends=True))
