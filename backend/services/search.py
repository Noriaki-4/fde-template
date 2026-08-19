from sqlalchemy.orm import Session
from typing import List, Optional
import structlog
from backend.repositories.document import DocumentRepository
from backend.database.models import Document
from pydantic import BaseModel

logger = structlog.get_logger()

class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    metadata: Optional[dict] = None

class SearchService:
    """検索サービス"""

    def __init__(self, db: Session):
        self.db = db
        self.doc_repo = DocumentRepository(db)

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """全文検索 (Phase 1: DB直接検索, Phase 2: OpenSearch)"""
        logger.info("search_query", query=query, limit=limit)

        # Phase 1: PostgreSQL LIKE 検索
        results = self.doc_repo.search_by_content(query, skip=0, limit=limit)

        return [
            SearchResult(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                metadata=doc.doc_metadata
            )
            for doc in results
        ]

    async def index_document(self, doc_id: str, title: str, content: str, metadata: dict = None) -> bool:
        """ドキュメントをインデックス"""
        try:
            self.doc_repo.create_or_update(doc_id, title, content, metadata)
            logger.info("document_indexed", doc_id=doc_id)
            return True
        except Exception as e:
            logger.error("indexing_error", doc_id=doc_id, error=str(e))
            return False

    async def delete_index(self, doc_id: str) -> bool:
        """インデックスから削除"""
        try:
            result = self.doc_repo.delete(doc_id)
            logger.info("document_deleted", doc_id=doc_id)
            return result
        except Exception as e:
            logger.error("deletion_error", doc_id=doc_id, error=str(e))
            return False

    async def get_document(self, doc_id: str) -> Optional[SearchResult]:
        """ドキュメント取得"""
        doc = self.doc_repo.get_by_id(doc_id)
        if doc:
            return SearchResult(
                id=doc.id,
                title=doc.title,
                content=doc.content,
                metadata=doc.doc_metadata
            )
        return None
