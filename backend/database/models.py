from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(255), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class Config:
        from_attributes = True


class SearchIndex(Base):
    __tablename__ = "search_indices"

    id = Column(String(255), primary_key=True, index=True)
    doc_id = Column(String(255), nullable=False, index=True)
    index_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectConfig(Base):
    __tablename__ = "project_configs"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    config = Column(JSON, nullable=False)
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ---------------------------------------------------------------------------
# Job execution records — see adr/004-job-execution.md
#
# Status is NOT written by the job itself: it is updated by RunEventHandler from
# launcher / orchestrator events (local subprocess exit, ECS Task State Change),
# so a job killed by OOM or timeout still ends up "failed".
# ---------------------------------------------------------------------------


class JobRun(Base):
    __tablename__ = "job_runs"

    id = Column(String(64), primary_key=True)
    kind = Column(String(20), nullable=False, default="job")  # job | pipeline
    job_name = Column(String(255), nullable=False, index=True)  # job name, or pipeline name
    parent_run_id = Column(String(64), ForeignKey("job_runs.id"), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    params = Column(JSON, nullable=False, default=dict)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    launcher = Column(String(20), nullable=False, default="local")  # local | ecs
    external_id = Column(String(512), nullable=True)  # pid / ECS task ARN
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)


class RunArtifact(Base):
    __tablename__ = "run_artifacts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), ForeignKey("job_runs.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    uri = Column(String(1024), nullable=False)
    artifact_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# RAG document catalog — see adr/003-rag-data-layers.md
#
# Layers: raw/processed content in S3 (source of truth for content), this catalog
# in Postgres (source of truth for metadata/lineage), and derived search stores
# (OpenSearch / Neo4j / RDF) that can be rebuilt from the two.
# ---------------------------------------------------------------------------


class CatalogDocument(Base):
    __tablename__ = "catalog_documents"

    id = Column(String(255), primary_key=True)
    source_uri = Column(String(2048), nullable=False)
    content_hash = Column(String(128), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="active", index=True)  # active | deleted
    raw_uri = Column(String(1024), nullable=True)
    processed_uri = Column(String(1024), nullable=True)
    ingest_run_id = Column(String(64), ForeignKey("job_runs.id"), nullable=True, index=True)
    acl = Column(JSON, nullable=True)
    doc_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CatalogDocumentTarget(Base):
    """Sync state of one catalog document in one derived store (opensearch / neo4j / rdf ...)."""

    __tablename__ = "catalog_document_targets"

    document_id = Column(String(255), ForeignKey("catalog_documents.id"), primary_key=True)
    target = Column(String(50), primary_key=True)
    # pending | indexed | failed | pending_delete | deleted
    status = Column(String(20), nullable=False, default="pending", index=True)
    indexed_version = Column(Integer, nullable=True)
    last_run_id = Column(String(64), ForeignKey("job_runs.id"), nullable=True)
    error = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
