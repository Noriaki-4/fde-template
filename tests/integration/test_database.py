"""Integration tests for database layer.

Runs against DATABASE_URL and drops all tables afterwards — point it at a
disposable database (e.g. the local dev Postgres from docker compose).
"""

import pytest

from backend.database.db import SessionLocal, drop_db, init_db
from backend.database.models import Document
from backend.repositories.document import DocumentRepository


@pytest.mark.integration
class TestDocumentRepository:
    @pytest.fixture(autouse=True)
    def repo(self):
        drop_db()
        init_db()
        db = SessionLocal()
        yield DocumentRepository(db)
        db.close()
        drop_db()

    def test_create_document(self, repo):
        created = repo.create(
            Document(
                id="doc-1", title="Test Doc", content="Test content", doc_metadata={"tag": "test"}
            )
        )

        assert created.id == "doc-1"
        assert created.title == "Test Doc"
        assert created.doc_metadata == {"tag": "test"}

    def test_find_by_title(self, repo):
        repo.create(Document(id="doc-1", title="Unique Title", content="Content", doc_metadata={}))

        found = repo.find_by_title("Unique Title")
        assert found is not None
        assert found.title == "Unique Title"

    def test_search_by_content(self, repo):
        repo.create(Document(id="doc-1", title="Doc 1", content="Python programming"))
        repo.create(Document(id="doc-2", title="Doc 2", content="JavaScript basics"))

        results = repo.search_by_content("Python")
        assert len(results) == 1
        assert results[0].title == "Doc 1"

    def test_update_document(self, repo):
        repo.create(Document(id="doc-1", title="Original", content="Original content"))

        updated = repo.update("doc-1", {"content": "Updated content"})

        assert updated.content == "Updated content"
        assert updated.title == "Original"

    def test_update_unknown_field_rejected(self, repo):
        repo.create(Document(id="doc-1", title="Original", content="Original content"))

        with pytest.raises(ValueError):
            repo.update("doc-1", {"no_such_field": 1})

    def test_update_missing_returns_none(self, repo):
        assert repo.update("missing", {"content": "x"}) is None

    def test_delete_document(self, repo):
        repo.create(Document(id="doc-1", title="To Delete", content="Content"))

        assert repo.delete("doc-1") is True
        assert repo.get_by_id("doc-1") is None
