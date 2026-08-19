from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(255), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    doc_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class Config:
        from_attributes = True


class SearchIndex(Base):
    __tablename__ = "search_indices"

    id = Column(String(255), primary_key=True, index=True)
    doc_id = Column(String(255), nullable=False, index=True)
    index_name = Column(String(255), nullable=False, index=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectConfig(Base):
    __tablename__ = "project_configs"

    id = Column(String(255), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    config = Column(JSON, nullable=False)
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
