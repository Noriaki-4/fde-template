import pytest
from tests.conftest import client

@pytest.mark.asyncio
def test_search_empty(client):
    """空のクエリで検索"""
    response = client.post("/search/", json={"query": "", "limit": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == ""
    assert data["total"] == 0
    assert data["results"] == []

@pytest.mark.asyncio
def test_index_document(client):
    """ドキュメントをインデックス"""
    payload = {
        "doc_id": "doc-1",
        "title": "Test Document",
        "content": "This is a test document",
        "metadata": {"source": "test"}
    }
    response = client.post("/search/index", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["doc_id"] == "doc-1"

@pytest.mark.asyncio
def test_get_document(client):
    """ドキュメントを取得"""
    # まずインデックス
    payload = {
        "doc_id": "doc-1",
        "title": "Test Document",
        "content": "This is a test document",
        "metadata": {"source": "test"}
    }
    client.post("/search/index", json=payload)

    # 取得
    response = client.get("/search/doc-1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "doc-1"
    assert data["title"] == "Test Document"

@pytest.mark.asyncio
def test_get_document_not_found(client):
    """ドキュメントが見つからない"""
    response = client.get("/search/nonexistent")
    assert response.status_code == 404

@pytest.mark.asyncio
def test_delete_document(client):
    """ドキュメントを削除"""
    # まずインデックス
    payload = {
        "doc_id": "doc-1",
        "title": "Test Document",
        "content": "This is a test document"
    }
    client.post("/search/index", json=payload)

    # 削除
    response = client.delete("/search/doc-1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # 削除確認
    response = client.get("/search/doc-1")
    assert response.status_code == 404
