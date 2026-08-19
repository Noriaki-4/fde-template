"""Graph and RDF Query Routes (Phase 3)"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.config import get_config
from backend.services.graph import GraphService
from backend.services.rdf import RDFService

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    params: dict[str, Any] | None = None


class TripleRequest(BaseModel):
    subject: str
    predicate: str
    object: str


async def get_graph_service(config=Depends(get_config)) -> GraphService | None:
    """Get graph service from app state"""
    from backend.api.main import get_graph_service

    return get_graph_service()


async def get_rdf_service(config=Depends(get_config)) -> RDFService | None:
    """Get RDF service from app state"""
    from backend.api.main import get_rdf_service

    return get_rdf_service()


@router.post("/query/cypher")
async def query_cypher(
    request: QueryRequest, service: GraphService | None = Depends(get_graph_service)
) -> dict[str, Any]:
    """Execute openCypher query against Neo4j"""
    if not service:
        raise HTTPException(status_code=503, detail="Graph service not configured")

    try:
        result = await service.query(request.query, request.params)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/sparql")
async def query_sparql(
    request: QueryRequest, service: RDFService | None = Depends(get_rdf_service)
) -> dict[str, Any]:
    """Execute SPARQL query against Virtuoso"""
    if not service:
        raise HTTPException(status_code=503, detail="RDF service not configured")

    try:
        result = await service.query(request.query, request.params)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/triples/insert")
async def insert_triples(
    triples: list[TripleRequest], service: RDFService | None = Depends(get_rdf_service)
) -> dict[str, Any]:
    """Insert RDF triples"""
    if not service:
        raise HTTPException(status_code=503, detail="RDF service not configured")

    try:
        triple_list = [(t.subject, t.predicate, t.object) for t in triples]
        success = await service.insert(triple_list)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/triples/{subject}")
async def delete_triples(
    subject: str,
    predicate: str | None = None,
    obj: str | None = None,
    service: RDFService | None = Depends(get_rdf_service),
) -> dict[str, Any]:
    """Delete RDF triples"""
    if not service:
        raise HTTPException(status_code=503, detail="RDF service not configured")

    try:
        success = await service.delete(subject, predicate, obj)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
