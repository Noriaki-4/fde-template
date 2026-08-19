from typing import List, Optional

from sqlalchemy.orm import Session

from backend.database.models import Document
from backend.repositories.base import Repository


class DocumentRepository(Repository[Document]):
    """Document Repository"""

    def __init__(self, db: Session):
        super().__init__(db, Document)

    def find_by_title(self, title: str) -> Optional[Document]:
        """タイトルで検索"""
        return self.db.query(Document).filter(Document.title == title).first()

    def search_by_content(self, keyword: str, skip: int = 0, limit: int = 100) -> List[Document]:
        """コンテンツで全文検索 (Phase 2: OpenSearch に移行予定)"""
        return (
            self.db.query(Document)
            .filter(Document.content.ilike(f"%{keyword}%"))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def find_by_metadata(self, key: str, value: str) -> List[Document]:
        """メタデータで検索"""
        # SQLAlchemy JSON フィルタリング
        return self.db.query(Document).filter(Document.doc_metadata[key].astext == value).all()

    def create_or_update(
        self, doc_id: str, title: str, content: str, metadata: dict = None
    ) -> Document:
        """作成または更新"""
        doc = self.get_by_id(doc_id)
        if doc:
            doc.title = title
            doc.content = content
            if metadata:
                doc.doc_metadata = metadata
            self.db.commit()
            self.db.refresh(doc)
            return doc
        else:
            new_doc = Document(id=doc_id, title=title, content=content, doc_metadata=metadata or {})
            return self.create(new_doc)
