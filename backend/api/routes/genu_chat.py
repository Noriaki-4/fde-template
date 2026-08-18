"""GenU-Compatible Chat API Routes (Phase 9)"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Any
from datetime import datetime

from backend.config import get_config

router = APIRouter()


class Message(BaseModel):
    """Chat message"""

    role: str  # user | assistant
    content: str


class Conversation(BaseModel):
    """Conversation metadata"""

    id: str
    title: str
    created_at: str
    messages: list[Message] = []


class ChatRequest(BaseModel):
    """Chat message request"""

    conversation_id: str
    message: str
    model: str | None = None


class ChatResponse(BaseModel):
    """Chat response"""

    conversation_id: str
    message: str
    role: str = "assistant"
    timestamp: str


# In-memory store (replace with database in production)
conversations: dict[str, Conversation] = {}


@router.post("/conversations")
async def create_conversation(config=Depends(get_config)) -> Conversation:
    """Create new conversation"""
    import uuid

    conv_id = str(uuid.uuid4())
    conversation = Conversation(
        id=conv_id,
        title="New Conversation",
        created_at=datetime.utcnow().isoformat(),
    )
    conversations[conv_id] = conversation
    return conversation


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str) -> Conversation:
    """Get conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversations[conversation_id]


@router.get("/conversations")
async def list_conversations() -> list[Conversation]:
    """List all conversations"""
    return list(conversations.values())


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: ChatRequest,
    config=Depends(get_config),
) -> ChatResponse:
    """Send message to conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = conversations[conversation_id]

    # Add user message
    conversation.messages.append(Message(role="user", content=request.message))

    # Generate response (mock - replace with actual service call)
    response_text = f"Echo: {request.message}"

    # Add assistant message
    assistant_msg = Message(role="assistant", content=response_text)
    conversation.messages.append(assistant_msg)

    return ChatResponse(
        conversation_id=conversation_id,
        message=response_text,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict[str, str]:
    """Delete conversation"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    del conversations[conversation_id]
    return {"status": "deleted"}
