from abc import ABC
from typing import Generic, List, Optional, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Base Repository クラス"""

    def __init__(self, db: Session, model: type):
        self.db = db
        self.model = model

    def create(self, obj: T) -> T:
        """作成"""
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def get_by_id(self, id: str) -> Optional[T]:
        """ID で取得"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """全件取得"""
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def update(self, id: str, obj: T) -> Optional[T]:
        """更新"""
        db_obj = self.get_by_id(id)
        if db_obj:
            for key, value in obj.dict(exclude_unset=True).items():
                setattr(db_obj, key, value)
            self.db.commit()
            self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: str) -> bool:
        """削除"""
        db_obj = self.get_by_id(id)
        if db_obj:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        return False

    def count(self) -> int:
        """件数"""
        return self.db.query(self.model).count()
