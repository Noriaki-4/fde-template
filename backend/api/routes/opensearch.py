"""OpenSearch Routes (Phase 2)"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.config import get_config
from backend.services.opensearch import OpenSearchInterface

router = APIRouter()


class IndexRequest(BaseModel):
    doc_id: str
    content: str
    metadata: dict[str, Any] | None = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


async def get_opensearch_service(config=Depends(get_config)) -> OpenSearchInterface | None:
    """Get OpenSearch service from app state"""
    from backend.api.main import get_opensearch_service as _get_opensearch_service

    return _get_opensearch_service()


@router.post("/index")
async def index_document(
    request: IndexRequest, service: OpenSearchInterface | None = Depends(get_opensearch_service)
) -> dict[str, Any]:
    """Index a document"""
    if not service:
        raise HTTPException(status_code=503, detail="OpenSearch service not configured")
    try:
        success = await service.index(request.doc_id, request.content, request.metadata)
        return {"success": success, "doc_id": request.doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def search_documents(
    request: SearchRequest, service: OpenSearchInterface | None = Depends(get_opensearch_service)
) -> dict[str, Any]:
    """Search indexed documents"""
    if not service:
        raise HTTPException(status_code=503, detail="OpenSearch service not configured")
    try:
        results = await service.search(request.query, request.limit)
        return {"query": request.query, "results": results, "total": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str, service: OpenSearchInterface | None = Depends(get_opensearch_service)
) -> dict[str, Any]:
    """Delete an indexed document"""
    if not service:
        raise HTTPException(status_code=503, detail="OpenSearch service not configured")
    try:
        success = await service.delete(doc_id)
        return {"success": success, "doc_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def opensearch_health(
    service: OpenSearchInterface | None = Depends(get_opensearch_service),
) -> dict[str, Any]:
    """Check OpenSearch backend health"""
    if not service:
        raise HTTPException(status_code=503, detail="OpenSearch service not configured")
    try:
        healthy = await service.health_check()
        return {"healthy": healthy}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
