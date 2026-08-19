"""Integration tests for database layer"""

import pytest

from backend.database.db import SessionLocal, drop_db, init_db
from backend.database.models import Document
from backend.repositories.document import DocumentRepository


@pytest.mark.integration
class TestDocumentRepository:
    @pytest.fixture(autouse=True)
    async def setup(self):
        await init_db()
        yield
        await drop_db()

    def test_create_document(self):
        db = SessionLocal()
        repo = DocumentRepository(db)

        doc = Document(
            title="Test Doc",
            content="Test content",
            metadata={"tag": "test"},
        )
        created = repo.create(doc)

        assert created.title == "Test Doc"
        assert created.id is not None

    def test_find_by_title(self):
        db = SessionLocal()
        repo = DocumentRepository(db)

        doc = Document(
            title="Unique Title",
            content="Content",
            metadata={},
        )
        repo.create(doc)

        found = repo.find_by_title("Unique Title")
        assert found is not None
        assert found.title == "Unique Title"

    def test_search_by_content(self):
        db = SessionLocal()
        repo = DocumentRepository(db)

        doc1 = Document(
            title="Doc 1",
            content="Python programming",
            metadata={},
        )
        doc2 = Document(
            title="Doc 2",
            content="JavaScript basics",
            metadata={},
        )
        repo.create(doc1)
        repo.create(doc2)

        results = repo.search_by_content("Python")
        assert len(results) == 1
        assert results[0].title == "Doc 1"

    def test_update_document(self):
        db = SessionLocal()
        repo = DocumentRepository(db)

        doc = Document(
            title="Original",
            content="Original content",
            metadata={},
        )
        created = repo.create(doc)

        created.content = "Updated content"
        updated = repo.update(created.id, created)

        assert updated.content == "Updated content"

    def test_delete_document(self):
        db = SessionLocal()
        repo = DocumentRepository(db)

        doc = Document(
            title="To Delete",
            content="Content",
            metadata={},
        )
        created = repo.create(doc)

        repo.delete(created.id)

        found = repo.get_by_id(created.id)
        assert found is None
