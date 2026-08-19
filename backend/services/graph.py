"""Graph Service for Phase 3"""

from abc import ABC, abstractmethod
from typing import Any


class GraphService(ABC):
    """Abstract Graph Service Interface"""

    @abstractmethod
    async def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Execute graph query"""
        pass

    @abstractmethod
    async def create_node(self, label: str, properties: dict[str, Any]) -> dict[str, Any]:
        """Create graph node"""
        pass

    @abstractmethod
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create relationship between nodes"""
        pass

    @abstractmethod
    async def delete_node(self, node_id: str) -> bool:
        """Delete node"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check graph database health"""
        pass


class Neo4jGraphService(GraphService):
    """Neo4j Graph Database Implementation"""

    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self._driver = None

    async def _get_driver(self):
        if not self._driver:
            from neo4j import AsyncGraphDatabase

            self._driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
        return self._driver

    async def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict]:
        driver = await self._get_driver()
        async with driver.session() as session:
            result = await session.run(cypher, params or {})
            return [dict(record) for record in await result.fetch(100)]

    async def create_node(self, label: str, properties: dict[str, Any]) -> dict[str, Any]:
        cypher = f"CREATE (n:{label} {{{','.join(f'{k}:${k}' for k in properties)}}}) RETURN n"
        result = await self.query(cypher, properties)
        return result[0] if result else {}

    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        cypher = f"MATCH (a), (b) WHERE a.id=$source_id AND b.id=$target_id CREATE (a)-[r:{relation}]->(b) RETURN r"
        result = await self.query(
            cypher, {"source_id": source_id, "target_id": target_id} | (properties or {})
        )
        return result[0] if result else {}

    async def delete_node(self, node_id: str) -> bool:
        cypher = "MATCH (n) WHERE n.id=$id DETACH DELETE n"
        await self.query(cypher, {"id": node_id})
        return True

    async def health_check(self) -> bool:
        try:
            result = await self.query("RETURN 1")
            return len(result) > 0
        except Exception:
            return False

    async def close(self):
        if self._driver:
            await self._driver.close()
