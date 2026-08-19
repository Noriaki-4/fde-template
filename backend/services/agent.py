"""Agent Service for Phase 4

Canonical Agent interface for this codebase. `backend/agent/agentcore.py`'s
`AgentCoreService` implements this same ABC for AWS Bedrock AgentCore.
"""

from abc import ABC, abstractmethod
from typing import Any


class AgentService(ABC):
    """Abstract Agent Service Interface"""

    @abstractmethod
    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Invoke agent with query"""
        pass

    @abstractmethod
    async def stream(self, query: str, context: dict[str, Any] | None = None):
        """Stream agent response"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check agent health"""
        pass


class LocalAgentService(AgentService):
    """Local (no external dependency) Agent Implementation — echoes the query"""

    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute query and return result"""
        return {"query": query, "response": f"Response to: {query}", "success": True}

    async def stream(self, query: str, context: dict[str, Any] | None = None):
        """Stream query results word-by-word"""
        for word in query.split():
            yield word + " "

    async def health_check(self) -> bool:
        """Local implementation is always available"""
        return True
