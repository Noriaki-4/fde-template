"""RDF/SPARQL Service for Phase 3"""

from abc import ABC, abstractmethod
from typing import Any


class RDFService(ABC):
    """Abstract RDF Service Interface"""

    @abstractmethod
    async def query(self, sparql: str, params: dict[str, Any] | None = None) -> list[dict]:
        """Execute SPARQL query"""
        pass

    @abstractmethod
    async def insert(self, triples: list[tuple[str, str, str]]) -> bool:
        """Insert RDF triples (subject, predicate, object)"""
        pass

    @abstractmethod
    async def delete(
        self, subject: str, predicate: str | None = None, obj: str | None = None
    ) -> bool:
        """Delete RDF triples"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check RDF store health"""
        pass


class VirtuosoRDFService(RDFService):
    """Virtuoso RDF Triple Store Implementation"""

    def __init__(self, sparql_endpoint: str):
        self.sparql_endpoint = sparql_endpoint
        self._client = None

    async def _get_client(self):
        if not self._client:
            import httpx

            self._client = httpx.AsyncClient(base_url=self.sparql_endpoint)
        return self._client

    async def query(self, sparql: str, params: dict[str, Any] | None = None) -> list[dict]:
        try:
            client = await self._get_client()
            response = await client.post(
                "/sparql",
                data={"query": sparql},
                params={"format": "json"},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("results", {}).get("bindings", [])
        except Exception:
            return []

    async def insert(self, triples: list[tuple[str, str, str]]) -> bool:
        try:
            # Build SPARQL INSERT DATA query
            triple_patterns = []
            for subject, predicate, obj in triples:
                triple_patterns.append(f"<{subject}> <{predicate}> <{obj}> .")

            sparql = f"""
            INSERT DATA {{
                GRAPH <http://fde.local/graph> {{
                    {chr(10).join(triple_patterns)}
                }}
            }}
            """

            client = await self._get_client()
            response = await client.post(
                "/sparql",
                data={"query": sparql},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def delete(
        self, subject: str, predicate: str | None = None, obj: str | None = None
    ) -> bool:
        try:
            # Build SPARQL DELETE WHERE query
            pattern = f"<{subject}>"
            if predicate:
                pattern += f" <{predicate}>"
            if obj:
                pattern += f" <{obj}>"
            pattern += " ."

            sparql = f"""
            DELETE WHERE {{
                GRAPH <http://fde.local/graph> {{
                    {pattern}
                }}
            }}
            """

            client = await self._get_client()
            response = await client.post(
                "/sparql",
                data={"query": sparql},
            )
            return response.status_code == 200
        except Exception:
            return False

    async def health_check(self) -> bool:
        try:
            client = await self._get_client()
            response = await client.get("/sparql?query=SELECT%201%20WHERE%20%7B%7D")
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._client:
            await self._client.aclose()
