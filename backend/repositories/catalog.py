"""RAG document catalog (adr/003-rag-data-layers.md).

The catalog is the source of truth for document metadata and lineage. Derived
search stores (OpenSearch / Neo4j / RDF) are tracked per document in
``catalog_document_targets`` so ingest jobs can find what needs (re)indexing or
deletion, and any store can be rebuilt from S3 content + this catalog.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.database.models import CatalogDocument, CatalogDocumentTarget

TARGET_PENDING = "pending"
TARGET_INDEXED = "indexed"
TARGET_FAILED = "failed"
TARGET_PENDING_DELETE = "pending_delete"
TARGET_DELETED = "deleted"
TARGET_STATUSES = frozenset(
    {TARGET_PENDING, TARGET_INDEXED, TARGET_FAILED, TARGET_PENDING_DELETE, TARGET_DELETED}
)


@dataclass(frozen=True)
class UpsertResult:
    document: CatalogDocument
    changed: bool  # True when new, or content hash changed (targets need reindex)


class CatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, doc_id: str) -> CatalogDocument | None:
        return self.db.query(CatalogDocument).filter(CatalogDocument.id == doc_id).first()

    def upsert_document(
        self,
        doc_id: str,
        source_uri: str,
        content_hash: str,
        targets: list[str],
        run_id: str | None = None,
        raw_uri: str | None = None,
        processed_uri: str | None = None,
        metadata: dict[str, Any] | None = None,
        acl: dict[str, Any] | None = None,
    ) -> UpsertResult:
        """Register a document. Unchanged content is a no-op (changed=False)."""
        doc = self.get(doc_id)
        if doc is not None and doc.content_hash == content_hash and doc.status == "active":
            return UpsertResult(document=doc, changed=False)

        if doc is None:
            doc = CatalogDocument(id=doc_id, version=1)
            self.db.add(doc)
        else:
            doc.version = doc.version + 1
        doc.source_uri = source_uri
        doc.content_hash = content_hash
        doc.status = "active"
        doc.raw_uri = raw_uri
        doc.processed_uri = processed_uri
        doc.ingest_run_id = run_id
        doc.doc_metadata = metadata
        doc.acl = acl
        self.db.flush()
        for target in targets:
            self._set_target(doc_id, target, TARGET_PENDING, run_id, error=None)
        self.db.commit()
        self.db.refresh(doc)
        return UpsertResult(document=doc, changed=True)

    def mark_deleted(self, doc_id: str, run_id: str | None = None) -> bool:
        """Soft-delete; every target becomes pending_delete for a sync job to process."""
        doc = self.get(doc_id)
        if doc is None:
            return False
        doc.status = "deleted"
        for target in self.list_targets(doc_id):
            target.status = TARGET_PENDING_DELETE
            target.last_run_id = run_id
        self.db.commit()
        return True

    def mark_target(
        self,
        doc_id: str,
        target: str,
        status: str,
        run_id: str | None = None,
        error: str | None = None,
    ) -> CatalogDocumentTarget:
        if status not in TARGET_STATUSES:
            raise ValueError(f"Unknown target status: {status}")
        row = self._set_target(doc_id, target, status, run_id, error)
        if status == TARGET_INDEXED:
            doc = self.get(doc_id)
            row.indexed_version = doc.version if doc else None
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_targets(self, doc_id: str) -> list[CatalogDocumentTarget]:
        return (
            self.db.query(CatalogDocumentTarget)
            .filter(CatalogDocumentTarget.document_id == doc_id)
            .all()
        )

    def find_by_target_status(
        self, target: str, status: str, limit: int = 100
    ) -> list[CatalogDocument]:
        """e.g. ("opensearch", "pending") -> documents an indexing job should process."""
        return (
            self.db.query(CatalogDocument)
            .join(CatalogDocumentTarget, CatalogDocumentTarget.document_id == CatalogDocument.id)
            .filter(CatalogDocumentTarget.target == target)
            .filter(CatalogDocumentTarget.status == status)
            .limit(limit)
            .all()
        )

    def list_by_run(self, run_id: str) -> list[CatalogDocument]:
        return self.db.query(CatalogDocument).filter(CatalogDocument.ingest_run_id == run_id).all()

    def _set_target(
        self, doc_id: str, target: str, status: str, run_id: str | None, error: str | None
    ) -> CatalogDocumentTarget:
        row = (
            self.db.query(CatalogDocumentTarget)
            .filter(CatalogDocumentTarget.document_id == doc_id)
            .filter(CatalogDocumentTarget.target == target)
            .first()
        )
        if row is None:
            row = CatalogDocumentTarget(document_id=doc_id, target=target)
            self.db.add(row)
        row.status = status
        row.last_run_id = run_id
        row.error = error
        return row
