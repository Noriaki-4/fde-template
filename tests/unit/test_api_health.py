import pytest
from tests.conftest import client

def test_health_check(client):
    """ヘルスチェック API テスト"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
