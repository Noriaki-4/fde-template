"""Unified RAG Routes - Search + Graph Integration"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Any
from pydantic import BaseModel

from backend.database.db import get_db
from backend.services.search import SearchService
from backend.services.graph import GraphService
from backend.services.rdf import RDFService
from backend.services.rag import RAGService

router = APIRouter()


class RAGSearchRequest(BaseModel):
    query: str
    include_graph: bool = False


async def get_rag_service(db: Session = Depends(get_db)) -> RAGService:
    """Build RAG service from per-request search session and app-wide graph/rdf services"""
    from backend.api.main import get_graph_service, get_rdf_service

    return RAGService(
        search_service=SearchService(db),
        graph_service=get_graph_service(),
        rdf_service=get_rdf_service(),
    )


@router.post("/search")
async def rag_search(
    request: RAGSearchRequest, service: RAGService = Depends(get_rag_service)
) -> dict[str, Any]:
    """Unified search across documents, graph, and RDF sources"""
    try:
        return await service.search(request.query, include_graph=request.include_graph)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/{entity_id}")
async def rag_context(
    entity_id: str, service: RAGService = Depends(get_rag_service)
) -> dict[str, Any]:
    """Get full context for an entity from all sources"""
    try:
        return await service.get_context(entity_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def rag_health(service: RAGService = Depends(get_rag_service)) -> dict[str, Any]:
    """Check health of all RAG sub-services"""
    return await service.health_check()
