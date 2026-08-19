"""NoSQL Data Access Routes (Phase 7)"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Any
from pydantic import BaseModel

from backend.config import get_config
from backend.database.nosql.base import NoSQLRepository

router = APIRouter()


class PutItemRequest(BaseModel):
    key: str
    item: dict[str, Any]


class QueryRequest(BaseModel):
    index: str
    condition: dict[str, Any] | None = None


class BatchWriteRequest(BaseModel):
    items: list[dict[str, Any]]


async def get_nosql_service(config=Depends(get_config)) -> NoSQLRepository | None:
    """Get NoSQL service from app state"""
    from backend.api.main import get_nosql_service as _get_nosql_service
    return _get_nosql_service()


@router.post("/items")
async def put_item(
    request: PutItemRequest, service: NoSQLRepository | None = Depends(get_nosql_service)
) -> dict[str, Any]:
    """Insert or update an item"""
    if not service:
        raise HTTPException(status_code=503, detail="NoSQL service not configured")
    try:
        success = await service.put_item(request.key, request.item)
        return {"success": success, "key": request.key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/items/{key}")
async def get_item(
    key: str, service: NoSQLRepository | None = Depends(get_nosql_service)
) -> dict[str, Any]:
    """Retrieve item by key"""
    if not service:
        raise HTTPException(status_code=503, detail="NoSQL service not configured")
    try:
        item = await service.get_item(key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"key": key, "item": item}


@router.post("/query")
async def query_items(
    request: QueryRequest, service: NoSQLRepository | None = Depends(get_nosql_service)
) -> dict[str, Any]:
    """Query items by index/condition"""
    if not service:
        raise HTTPException(status_code=503, detail="NoSQL service not configured")
    try:
        items = await service.query(request.index, request.condition or {})
        return {"success": True, "items": items, "count": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/items/{key}")
async def delete_item(
    key: str, service: NoSQLRepository | None = Depends(get_nosql_service)
) -> dict[str, Any]:
    """Delete item"""
    if not service:
        raise HTTPException(status_code=503, detail="NoSQL service not configured")
    try:
        success = await service.delete_item(key)
        return {"success": success, "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def batch_write(
    request: BatchWriteRequest, service: NoSQLRepository | None = Depends(get_nosql_service)
) -> dict[str, Any]:
    """Batch write multiple items"""
    if not service:
        raise HTTPException(status_code=503, detail="NoSQL service not configured")
    try:
        success = await service.batch_write(request.items)
        return {"success": success, "count": len(request.items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def nosql_health(
    service: NoSQLRepository | None = Depends(get_nosql_service),
) -> dict[str, Any]:
    """Check NoSQL backend health"""
    if not service:
        raise HTTPException(status_code=503, detail="NoSQL service not configured")
    try:
        healthy = await service.health_check()
        return {"healthy": healthy}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
