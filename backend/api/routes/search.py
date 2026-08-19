from typing import List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.services.search import SearchResult, SearchService

router = APIRouter()
logger = structlog.get_logger()


class IndexRequest(BaseModel):
    doc_id: str
    title: str
    content: str
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest, db: Session = Depends(get_db)):
    """ドキュメント検索"""
    try:
        service = SearchService(db)
        results = await service.search(request.query, limit=request.limit)
        return SearchResponse(query=request.query, results=results, total=len(results))
    except Exception as e:
        logger.error("search_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index", response_model=dict)
async def index_document(request: IndexRequest, db: Session = Depends(get_db)):
    """ドキュメントをインデックス"""
    try:
        service = SearchService(db)
        success = await service.index_document(
            request.doc_id, request.title, request.content, request.metadata
        )
        return {"success": success, "doc_id": request.doc_id}
    except Exception as e:
        logger.error("indexing_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", response_model=SearchResult)
async def get_document(doc_id: str, db: Session = Depends(get_db)):
    """ドキュメント取得"""
    service = SearchService(db)
    result = await service.get_document(doc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")
    return result


@router.delete("/{doc_id}", response_model=dict)
async def delete_document(doc_id: str, db: Session = Depends(get_db)):
    """ドキュメント削除"""
    try:
        service = SearchService(db)
        success = await service.delete_index(doc_id)
        return {"success": success, "doc_id": doc_id}
    except Exception as e:
        logger.error("deletion_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
