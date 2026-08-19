from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from backend.config import get_config
from backend.database.models import Base

config = get_config()
engine = create_engine(
    config.database_url,
    echo=config.debug,
    poolclass=NullPool if config.database_url.startswith("sqlite") else None,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Database スキーマ作成"""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Database スキーマ削除 (開発用)"""
    Base.metadata.drop_all(bind=engine)
