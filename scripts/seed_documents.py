#!/usr/bin/env python3
"""Seed sample documents into database"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import Settings
from backend.database.db import SessionLocal, init_db
from backend.database.models import Document
from backend.repositories.document import DocumentRepository


async def seed_documents():
    """Create sample documents"""
    await init_db()

    db = SessionLocal()
    repo = DocumentRepository(db)

    documents = [
        {
            "title": "FastAPI Basics",
            "content": "FastAPI is a modern web framework for building APIs with Python 3.7+",
            "metadata": {"category": "tutorial", "language": "en"},
        },
        {
            "title": "Database Design",
            "content": "Designing databases requires careful consideration of schemas and indexing",
            "metadata": {"category": "guide", "language": "en"},
        },
        {
            "title": "Neo4j Graph Queries",
            "content": "Cypher is the query language for Neo4j graph database operations",
            "metadata": {"category": "reference", "language": "en"},
        },
    ]

    for doc in documents:
        existing = repo.find_by_title(doc["title"])
        if not existing:
            repo.create(
                Document(
                    title=doc["title"],
                    content=doc["content"],
                    metadata=doc["metadata"],
                )
            )
            print(f"✓ Created: {doc['title']}")
        else:
            print(f"- Skipped: {doc['title']} (exists)")

    db.close()
    print("✓ Seeding complete")


if __name__ == "__main__":
    asyncio.run(seed_documents())
