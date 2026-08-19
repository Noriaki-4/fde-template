"""Tests for NoSQL Data Access Routes"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes.nosql import get_nosql_service
from backend.database.nosql.base import NoSQLRepository


class FakeNoSQLService(NoSQLRepository):
    """In-memory fake used to test the /nosql routes without real boto3 calls"""

    def __init__(self):
        self.store: dict = {}

    async def put_item(self, key: str, item: dict) -> bool:
        self.store[key] = item
        return True

    async def get_item(self, key: str) -> dict | None:
        return self.store.get(key)

    async def query(self, index: str, condition: dict) -> list[dict]:
        return [v for k, v in self.store.items() if k == index]

    async def delete_item(self, key: str) -> bool:
        return self.store.pop(key, None) is not None

    async def batch_write(self, items: list[dict]) -> bool:
        for item in items:
            pk = item.get("pk")
            if pk:
                self.store[pk] = item
        return True

    async def health_check(self) -> bool:
        return True


@pytest.mark.unit
class TestNoSQLRoutes:
    @pytest.fixture
    def fake_service(self):
        return FakeNoSQLService()

    @pytest.fixture
    def client(self, fake_service):
        app.dependency_overrides[get_nosql_service] = lambda: fake_service
        yield TestClient(app)
        app.dependency_overrides.pop(get_nosql_service, None)

    def test_put_and_get_item(self, client):
        put_response = client.post(
            "/nosql/items", json={"key": "item-1", "item": {"name": "test"}}
        )
        assert put_response.status_code == 200
        assert put_response.json()["success"] is True

        get_response = client.get("/nosql/items/item-1")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["key"] == "item-1"
        assert data["item"]["name"] == "test"

    def test_get_item_not_found(self, client):
        response = client.get("/nosql/items/nonexistent")
        assert response.status_code == 404

    def test_delete_item(self, client):
        client.post("/nosql/items", json={"key": "item-2", "item": {"a": 1}})
        response = client.delete("/nosql/items/item-2")
        assert response.status_code == 200
        assert response.json()["success"] is True

        get_response = client.get("/nosql/items/item-2")
        assert get_response.status_code == 404

    def test_query_items(self, client):
        client.post("/nosql/items", json={"key": "item-3", "item": {"a": 1}})
        response = client.post("/nosql/query", json={"index": "item-3", "condition": {}})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 1

    def test_batch_write(self, client):
        response = client.post(
            "/nosql/batch",
            json={"items": [{"pk": "b1", "a": 1}, {"pk": "b2", "a": 2}]},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_health_check(self, client):
        response = client.get("/nosql/health")
        assert response.status_code == 200
        assert response.json()["healthy"] is True

    def test_service_not_configured_returns_503(self):
        app.dependency_overrides[get_nosql_service] = lambda: None
        try:
            client = TestClient(app)
            response = client.get("/nosql/items/anything")
            assert response.status_code == 503
        finally:
            app.dependency_overrides.pop(get_nosql_service, None)
