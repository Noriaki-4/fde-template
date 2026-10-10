import pytest

from backend.repositories.catalog import CatalogRepository
from backend.repositories.job_run import JobRunRepository


@pytest.fixture
def repo(session_factory):
    db = session_factory()
    yield CatalogRepository(db)
    db.close()


@pytest.fixture
def run_id(session_factory):
    return JobRunRepository(session_factory()).create("ingest", {}, "local").id


def _targets(repo, doc_id):
    return {t.target: t.status for t in repo.list_targets(doc_id)}


def test_new_document_is_pending_for_all_targets(repo, run_id):
    result = repo.upsert_document(
        "doc-1",
        "https://example.com/a",
        "h1",
        ["opensearch", "neo4j"],
        run_id=run_id,
        raw_uri="s3://kb/raw/a.html",
        metadata={"lang": "ja"},
    )
    assert result.changed is True
    assert result.document.version == 1
    assert result.document.ingest_run_id == run_id
    assert _targets(repo, "doc-1") == {"opensearch": "pending", "neo4j": "pending"}


def test_same_hash_is_noop(repo):
    repo.upsert_document("doc-1", "u", "h1", ["opensearch"])
    repo.mark_target("doc-1", "opensearch", "indexed")
    result = repo.upsert_document("doc-1", "u", "h1", ["opensearch"])
    assert result.changed is False
    assert _targets(repo, "doc-1") == {"opensearch": "indexed"}


def test_changed_hash_bumps_version_and_requeues(repo):
    repo.upsert_document("doc-1", "u", "h1", ["opensearch"])
    repo.mark_target("doc-1", "opensearch", "indexed")
    result = repo.upsert_document("doc-1", "u", "h2", ["opensearch"])
    assert result.changed is True
    assert result.document.version == 2
    assert _targets(repo, "doc-1") == {"opensearch": "pending"}


def test_mark_indexed_records_version(repo, run_id):
    repo.upsert_document("doc-1", "u", "h1", ["opensearch"])
    row = repo.mark_target("doc-1", "opensearch", "indexed", run_id=run_id)
    assert row.indexed_version == 1
    assert row.last_run_id == run_id


def test_invalid_target_status(repo):
    repo.upsert_document("doc-1", "u", "h1", ["opensearch"])
    with pytest.raises(ValueError):
        repo.mark_target("doc-1", "opensearch", "done")


def test_delete_marks_targets_pending_delete(repo):
    repo.upsert_document("doc-1", "u", "h1", ["opensearch", "rdf"])
    assert repo.mark_deleted("doc-1") is True
    assert repo.get("doc-1").status == "deleted"
    assert set(_targets(repo, "doc-1").values()) == {"pending_delete"}
    assert repo.mark_deleted("missing") is False


def test_reupsert_after_delete_reactivates(repo):
    repo.upsert_document("doc-1", "u", "h1", ["opensearch"])
    repo.mark_deleted("doc-1")
    result = repo.upsert_document("doc-1", "u", "h1", ["opensearch"])
    assert result.changed is True
    assert result.document.status == "active"


def test_find_by_target_status_and_by_run(repo, run_id):
    repo.upsert_document("doc-1", "u1", "h1", ["opensearch"], run_id=run_id)
    repo.upsert_document("doc-2", "u2", "h2", ["opensearch"])
    repo.mark_target("doc-2", "opensearch", "indexed")
    assert [d.id for d in repo.find_by_target_status("opensearch", "pending")] == ["doc-1"]
    assert [d.id for d in repo.list_by_run(run_id)] == ["doc-1"]
