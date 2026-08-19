"""Tests for Unified RAG Routes"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes.rag import get_rag_service
from backend.services.rag import RAGService


class FakeSearchService:
    """Minimal fake matching the subset of SearchService used by RAGService"""

    async def search(self, query: str, limit: int = 10):
        return [{"id": "doc-1", "title": "Test Doc", "content": query}]

    async def get_document(self, doc_id: str):
        return {"id": doc_id, "title": "Test Doc", "content": "content"}

    async def health_check(self) -> bool:
        return True


@pytest.mark.unit
class TestRAGRoutes:
    @pytest.fixture
    def fake_rag_service(self):
        return RAGService(search_service=FakeSearchService(), graph_service=None, rdf_service=None)

    @pytest.fixture
    def client(self, fake_rag_service):
        app.dependency_overrides[get_rag_service] = lambda: fake_rag_service
        yield TestClient(app)
        app.dependency_overrides.pop(get_rag_service, None)

    def test_rag_search(self, client):
        response = client.post("/rag/search", json={"query": "test", "include_graph": False})
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert len(data["search_results"]) == 1

    def test_rag_context(self, client):
        response = client.get("/rag/context/doc-1")
        assert response.status_code == 200
        data = response.json()
        assert data["entity_id"] == "doc-1"
        assert data["search"] is not None

    def test_rag_health(self, client):
        response = client.get("/rag/health")
        assert response.status_code == 200
        data = response.json()
        assert data["rag_available"] is True
        assert data["services"]["search"] is True
