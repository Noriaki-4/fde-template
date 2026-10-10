"""Runtime context handed to ``Job.run``."""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import structlog
from sqlalchemy.orm import Session

from backend.repositories.job_run import JobRunRepository
from backend.storage.object_store import ObjectStore

SessionFactory = Callable[[], Session]


class ArtifactStore:
    """Writes job outputs under ``runs/{root_run_id}/{job_name}/`` and records them.

    ``root_run_id`` is the pipeline run when the job runs as a pipeline step, so
    every step of one pipeline execution shares a prefix.
    """

    def __init__(
        self,
        store: ObjectStore,
        session_factory: SessionFactory,
        run_id: str,
        root_run_id: str,
        job_name: str,
    ):
        self._store = store
        self._session_factory = session_factory
        self._run_id = run_id
        self._root_run_id = root_run_id
        self.prefix = f"runs/{root_run_id}/{job_name}/"

    def find_upstream(self, name: str, job_name: str | None = None) -> str | None:
        """URI of the latest artifact ``name`` written by an earlier step of the same
        pipeline run (optionally only from ``job_name``). None outside a pipeline."""
        if self._root_run_id == self._run_id:
            return None
        db = self._session_factory()
        try:
            repo = JobRunRepository(db)
            siblings = repo.list_runs(parent_run_id=self._root_run_id, limit=1000)
            for run in siblings:  # newest first
                if run.id == self._run_id or (job_name and run.job_name != job_name):
                    continue
                for artifact in reversed(repo.list_artifacts(run.id)):
                    if artifact.name == name:
                        return artifact.uri
            return None
        finally:
            db.close()

    def put_bytes(
        self, name: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        if not name or name.startswith("/") or ".." in name.split("/"):
            raise ValueError(f"Invalid artifact name: {name!r}")
        uri = self._store.put_bytes(self.prefix + name, data, content_type)
        db = self._session_factory()
        try:
            JobRunRepository(db).add_artifact(self._run_id, name, uri, {"size": len(data)})
        finally:
            db.close()
        return uri

    def put_json(self, name: str, obj: Any) -> str:
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        return self.put_bytes(name, data, "application/json")

    def get_bytes(self, uri: str) -> bytes:
        return self._store.get_bytes(uri)

    def get_json(self, uri: str) -> Any:
        return json.loads(self.get_bytes(uri))


@dataclass(frozen=True)
class JobContext:
    run_id: str
    job_name: str
    params: Mapping[str, Any]
    parent_run_id: str | None
    artifacts: ArtifactStore
    session_factory: SessionFactory
    logger: Any

    @classmethod
    def create(
        cls,
        run_id: str,
        job_name: str,
        params: dict[str, Any],
        parent_run_id: str | None,
        store: ObjectStore,
        session_factory: SessionFactory,
    ) -> "JobContext":
        root = parent_run_id or run_id
        return cls(
            run_id=run_id,
            job_name=job_name,
            params=MappingProxyType(dict(params)),
            parent_run_id=parent_run_id,
            artifacts=ArtifactStore(store, session_factory, run_id, root, job_name),
            session_factory=session_factory,
            logger=structlog.get_logger().bind(run_id=run_id, job=job_name),
        )
