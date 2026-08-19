"""Tests for OpenSearch Routes"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes.opensearch import get_opensearch_service
from backend.services.opensearch import OpenSearchInterface


class FakeOpenSearchService(OpenSearchInterface):
    """In-memory fake used to test the /opensearch routes without a real cluster"""

    def __init__(self):
        self.store: dict = {}

    async def index(self, doc_id: str, content: str, metadata: dict | None = None) -> bool:
        self.store[doc_id] = {"content": content, **(metadata or {})}
        return True

    async def search(self, query: str, limit: int = 10) -> list[dict]:
        return [doc for doc in self.store.values() if query in doc.get("content", "")][:limit]

    async def delete(self, doc_id: str) -> bool:
        return self.store.pop(doc_id, None) is not None

    async def health_check(self) -> bool:
        return True


@pytest.mark.unit
class TestOpenSearchRoutes:
    @pytest.fixture
    def fake_service(self):
        return FakeOpenSearchService()

    @pytest.fixture
    def client(self, fake_service):
        app.dependency_overrides[get_opensearch_service] = lambda: fake_service
        yield TestClient(app)
        app.dependency_overrides.pop(get_opensearch_service, None)

    def test_index_document(self, client):
        response = client.post(
            "/opensearch/index", json={"doc_id": "doc-1", "content": "hello world"}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_search_documents(self, client):
        client.post("/opensearch/index", json={"doc_id": "doc-1", "content": "hello world"})
        response = client.post("/opensearch/search", json={"query": "hello", "limit": 10})
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_delete_document(self, client):
        client.post("/opensearch/index", json={"doc_id": "doc-2", "content": "to delete"})
        response = client.delete("/opensearch/doc-2")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_health_check(self, client):
        response = client.get("/opensearch/health")
        assert response.status_code == 200
        assert response.json()["healthy"] is True

    def test_service_not_configured_returns_503(self):
        app.dependency_overrides[get_opensearch_service] = lambda: None
        try:
            client = TestClient(app)
            response = client.get("/opensearch/health")
            assert response.status_code == 503
        finally:
            app.dependency_overrides.pop(get_opensearch_service, None)
