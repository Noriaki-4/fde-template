"""OpenSearch Service for Phase 2"""

from abc import ABC, abstractmethod
from typing import Any


class OpenSearchInterface(ABC):
    """Abstract OpenSearch Service Interface"""

    @abstractmethod
    async def index(self, doc_id: str, content: str, metadata: dict[str, Any] | None = None) -> bool:
        """Index document"""
        pass

    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search documents"""
        pass

    @abstractmethod
    async def delete(self, doc_id: str) -> bool:
        """Delete indexed document"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check search service health"""
        pass


class OpenSearchService(OpenSearchInterface):
    """OpenSearch Implementation"""

    def __init__(self, url: str, index: str = "documents"):
        self.url = url
        self.index = index
        self._client = None

    async def _get_client(self):
        if not self._client:
            from opensearchpy import OpenSearch

            self._client = OpenSearch([{"host": self.url.split("://")[1].split(":")[0], "port": 9200, "use_ssl": False}])
        return self._client

    async def index(self, doc_id: str, content: str, metadata: dict[str, Any] | None = None) -> bool:
        try:
            client = await self._get_client()
            doc = {"content": content, **(metadata or {})}
            client.index(index=self.index, id=doc_id, body=doc)
            return True
        except Exception:
            return False

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        try:
            client = await self._get_client()
            response = client.search(
                index=self.index,
                body={
                    "query": {"multi_match": {"query": query, "fields": ["content", "metadata"]}},
                    "size": limit,
                },
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception:
            return []

    async def delete(self, doc_id: str) -> bool:
        try:
            client = await self._get_client()
            client.delete(index=self.index, id=doc_id)
            return True
        except Exception:
            return False

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            info = client.info()
            return info.get("status") == 200
        except Exception:
            return False
