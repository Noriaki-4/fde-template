"""Agent Service for Phase 4"""

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
    """Local Agent Implementation"""

    def __init__(self, runtime):
        self.runtime = runtime

    async def invoke(self, query: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute query and return result"""
        return await self.runtime.invoke(query, context or {})

    async def stream(self, query: str, context: dict[str, Any] | None = None):
        """Stream query results"""
        async for chunk in self.runtime.stream(query, context or {}):
            yield chunk

    async def health_check(self) -> bool:
        """Verify runtime health"""
        return await self.runtime.health_check()
