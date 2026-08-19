#!/usr/bin/env python3
"""Seed sample graph nodes and relationships"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import Settings
from backend.services.graph import Neo4jGraphService


async def seed_graph():
    """Create sample graph nodes and relationships"""
    settings = Settings()

    if not settings.neo4j_uri:
        print("✗ Neo4j not configured")
        return

    service = Neo4jGraphService(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)

    # Create concept nodes
    concepts = [
        "Machine Learning",
        "Natural Language Processing",
        "Knowledge Graphs",
        "Vector Databases",
    ]

    for concept in concepts:
        cypher = "CREATE (c:Concept {name: $name}) RETURN c"
        result = await service.query(cypher, {"name": concept})
        if result:
            print(f"✓ Created concept: {concept}")

    # Create relationships
    relationships = [
        ("Machine Learning", "Natural Language Processing", "ENABLES"),
        ("Machine Learning", "Vector Databases", "USES"),
        ("Knowledge Graphs", "Vector Databases", "SUPPORTS"),
    ]

    for source, target, relation in relationships:
        cypher = f"""
        MATCH (a:Concept {{name: $source}})
        MATCH (b:Concept {{name: $target}})
        CREATE (a)-[:{relation}]->(b)
        RETURN a, b
        """
        result = await service.query(cypher, {"source": source, "target": target})
        if result:
            print(f"✓ Created relationship: {source} -[{relation}]-> {target}")

    await service.close()
    print("✓ Graph seeding complete")


if __name__ == "__main__":
    asyncio.run(seed_graph())
