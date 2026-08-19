"""Abstract NoSQL Repository"""

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class NoSQLRepository(ABC, Generic[T]):
    """Base NoSQL data access"""

    @abstractmethod
    async def put_item(self, key: str, item: dict[str, Any]) -> bool:
        """Insert or update item"""
        pass

    @abstractmethod
    async def get_item(self, key: str) -> dict[str, Any] | None:
        """Retrieve item by key"""
        pass

    @abstractmethod
    async def query(self, index: str, condition: dict[str, Any]) -> list[dict[str, Any]]:
        """Query items by condition"""
        pass

    @abstractmethod
    async def delete_item(self, key: str) -> bool:
        """Delete item"""
        pass

    @abstractmethod
    async def batch_write(self, items: list[dict[str, Any]]) -> bool:
        """Batch write multiple items"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check NoSQL service health"""
        pass
