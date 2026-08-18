from abc import ABC, abstractmethod
from typing import AsyncIterator, Dict, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class AgentRequest:
    user_input: str
    conversation_id: Optional[str] = None
    tools: Optional[list] = None
    metadata: Optional[dict] = None

@dataclass
class AgentResponse:
    content: str
    tool_calls: Optional[list] = None
    reasoning: Optional[str] = None
    stop_reason: str = "end_turn"

class AgentRuntime(ABC):
    @abstractmethod
    async def invoke(self, request: AgentRequest) -> AgentResponse:
        pass

    @abstractmethod
    async def stream(self, request: AgentRequest) -> AsyncIterator[AgentResponse]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass

class LocalAgentRuntime(AgentRuntime):
    def __init__(self):
        logger.info("LocalAgentRuntime initialized")

    async def invoke(self, request: AgentRequest) -> AgentResponse:
        logger.info("agent_invoke", input=request.user_input)
        return AgentResponse(
            content=f"Response to: {request.user_input}",
            stop_reason="end_turn"
        )

    async def stream(self, request: AgentRequest) -> AsyncIterator[AgentResponse]:
        async for chunk in self._generate_stream(request.user_input):
            yield AgentResponse(content=chunk)

    async def _generate_stream(self, text: str) -> AsyncIterator[str]:
        for word in text.split():
            yield word + " "

    async def health_check(self) -> bool:
        return True
