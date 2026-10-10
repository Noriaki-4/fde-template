"""Job interface. A concrete job implements ``run`` and is registered with ``@register_job``."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from backend.jobs.context import JobContext


class Job(ABC):
    name: ClassVar[str] = ""
    description: ClassVar[str] = ""

    @abstractmethod
    async def run(self, ctx: "JobContext") -> dict[str, Any]:
        """Do the work. Return a small JSON-serialisable summary (stored as the run result).

        Pass large data between jobs through ``ctx.artifacts`` (S3 / MinIO), never
        through the return value or local disk.
        """
