"""Tests for GenU Chat API"""

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes.genu_chat import get_llm_service
from backend.services.llm import LLMService


class FakeLLMService(LLMService):
    """In-memory fake used to test the /chat routes without a real LLM backend"""

    async def complete(self, prompt: str, **kwargs) -> str:
        return f"Echo: {prompt}"

    async def stream(self, prompt: str, **kwargs):
        yield f"Echo: {prompt}"

    async def health_check(self) -> bool:
        return True


@pytest.mark.unit
class TestGenUChat:
    @pytest.fixture
    def client(self):
        app.dependency_overrides[get_llm_service] = lambda: FakeLLMService()
        yield TestClient(app)
        app.dependency_overrides.pop(get_llm_service, None)

    def test_create_conversation(self, client):
        response = client.post("/chat/conversations")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "New Conversation"

    def test_get_conversation(self, client):
        # Create conversation
        create_response = client.post("/chat/conversations")
        conv_id = create_response.json()["id"]

        # Get conversation
        get_response = client.get(f"/chat/conversations/{conv_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == conv_id

    def test_list_conversations(self, client):
        response = client.get("/chat/conversations")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_send_message(self, client):
        # Create conversation
        create_response = client.post("/chat/conversations")
        conv_id = create_response.json()["id"]

        # Send message
        send_response = client.post(
            f"/chat/conversations/{conv_id}/messages",
            json={"conversation_id": conv_id, "message": "Hello"},
        )
        assert send_response.status_code == 200
        data = send_response.json()
        assert data["message"] is not None
        assert data["role"] == "assistant"

    def test_send_message_to_nonexistent_conversation(self, client):
        response = client.post(
            "/chat/conversations/nonexistent/messages",
            json={"conversation_id": "nonexistent", "message": "Hello"},
        )
        assert response.status_code == 404

    def test_delete_conversation(self, client):
        # Create conversation
        create_response = client.post("/chat/conversations")
        conv_id = create_response.json()["id"]

        # Delete conversation
        delete_response = client.delete(f"/chat/conversations/{conv_id}")
        assert delete_response.status_code == 200

        # Verify it's deleted
        get_response = client.get(f"/chat/conversations/{conv_id}")
        assert get_response.status_code == 404
