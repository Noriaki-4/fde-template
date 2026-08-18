"""Unified RAG Service - Search + Graph Integration"""

from typing import Any

from backend.services.search import SearchService
from backend.services.graph import GraphService
from backend.services.rdf import RDFService


class RAGService:
    """Unified RAG Interface combining Search and Graph"""

    def __init__(
        self,
        search_service: SearchService | None = None,
        graph_service: GraphService | None = None,
        rdf_service: RDFService | None = None,
    ):
        self.search_service = search_service
        self.graph_service = graph_service
        self.rdf_service = rdf_service

    async def search(
        self, query: str, include_graph: bool = False
    ) -> dict[str, Any]:
        """Unified search across all sources"""
        results = {"query": query, "search_results": [], "graph_results": []}

        # Search documents
        if self.search_service:
            try:
                search_results = await self.search_service.search(query)
                results["search_results"] = search_results
            except Exception as e:
                results["search_error"] = str(e)

        # Search graph if requested
        if include_graph:
            # Try Property Graph
            if self.graph_service:
                try:
                    cypher = f"""
                    MATCH (n) WHERE n.name CONTAINS '{query}' RETURN n
                    """
                    graph_results = await self.graph_service.query(cypher)
                    results["graph_results"].extend(graph_results)
                except Exception as e:
                    results["graph_error"] = str(e)

            # Try RDF
            if self.rdf_service:
                try:
                    sparql = f"""
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    SELECT ?s ?p ?o WHERE {{
                        ?s ?p ?o .
                        ?s rdfs:label ?label .
                        FILTER (CONTAINS(STR(?label), '{query}'))
                    }}
                    """
                    rdf_results = await self.rdf_service.query(sparql)
                    results["rdf_results"] = rdf_results
                except Exception as e:
                    results["rdf_error"] = str(e)

        return results

    async def get_context(self, entity_id: str) -> dict[str, Any]:
        """Get full context for entity from all sources"""
        context = {"entity_id": entity_id, "search": None, "graph": None, "rdf": None}

        # Get from search
        if self.search_service:
            try:
                context["search"] = await self.search_service.get_document(entity_id)
            except Exception:
                pass

        # Get from graph
        if self.graph_service:
            try:
                cypher = f"""
                MATCH (n) WHERE n.id = '{entity_id}'
                RETURN n
                """
                result = await self.graph_service.query(cypher)
                context["graph"] = result[0] if result else None
            except Exception:
                pass

        # Get from RDF
        if self.rdf_service:
            try:
                sparql = f"""
                SELECT ?p ?o WHERE {{
                    <{entity_id}> ?p ?o
                }}
                """
                result = await self.rdf_service.query(sparql)
                context["rdf"] = result
            except Exception:
                pass

        return context

    async def health_check(self) -> dict[str, bool]:
        """Check health of all services"""
        health = {"rag_available": False, "services": {}}

        if self.search_service:
            try:
                health["services"]["search"] = await self.search_service.health_check()
            except Exception:
                health["services"]["search"] = False

        if self.graph_service:
            try:
                health["services"]["graph"] = await self.graph_service.health_check()
            except Exception:
                health["services"]["graph"] = False

        if self.rdf_service:
            try:
                health["services"]["rdf"] = await self.rdf_service.health_check()
            except Exception:
                health["services"]["rdf"] = False

        # RAG is available if at least search or graph is available
        health["rag_available"] = any(health["services"].values())
        return health
