"""LLM Service for Phase 4"""

from abc import ABC, abstractmethod
from typing import Any


class LLMService(ABC):
    """Abstract LLM Service Interface"""

    @abstractmethod
    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Get completion for prompt"""
        pass

    @abstractmethod
    async def stream(self, prompt: str, **kwargs: Any):
        """Stream completion"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check LLM availability"""
        pass


class OllamaLLMService(LLMService):
    """Ollama Local LLM Implementation"""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url
        self.model = model

    async def complete(self, prompt: str, **kwargs: Any) -> str:
        """Generate completion using Ollama"""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
                timeout=300.0,
            )
            response.raise_for_status()
            return response.json().get("response", "")

    async def stream(self, prompt: str, **kwargs: Any):
        """Stream completion from Ollama"""
        import httpx

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": True},
                timeout=300.0,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        import json

                        data = json.loads(line)
                        yield data.get("response", "")

    async def health_check(self) -> bool:
        """Verify Ollama is running"""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/api/tags", timeout=5.0)
                return response.status_code == 200
        except Exception:
            return False


