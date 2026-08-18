from neo4j import GraphDatabase
from typing import List, Dict, Any
import structlog
from backend.config import get_config

logger = structlog.get_logger()

class Neo4jClient:
    def __init__(self):
        config = get_config()
        if not config.neo4j_enabled:
            self.driver = None
            return

        self.driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_user, config.neo4j_password)
        )

    def query(self, cypher: str, params: dict = None) -> List[Dict[str, Any]]:
        if not self.driver:
            return []
        try:
            with self.driver.session() as session:
                result = session.run(cypher, params or {})
                return [dict(record) for record in result]
        except Exception as e:
            logger.error("neo4j_query_error", error=str(e))
            return []

    def create_node(self, label: str, properties: dict) -> bool:
        if not self.driver:
            return False
        try:
            cypher = f"CREATE (n:{label} $props) RETURN n"
            with self.driver.session() as session:
                session.run(cypher, props=properties)
            logger.info("node_created", label=label)
            return True
        except Exception as e:
            logger.error("neo4j_create_error", error=str(e))
            return False

    def create_relationship(self, source_id: str, target_id: str, relation: str) -> bool:
        if not self.driver:
            return False
        try:
            cypher = f"""
            MATCH (a) WHERE a.id = $source_id
            MATCH (b) WHERE b.id = $target_id
            CREATE (a)-[:{relation}]->(b)
            """
            with self.driver.session() as session:
                session.run(cypher, source_id=source_id, target_id=target_id)
            return True
        except Exception as e:
            logger.error("neo4j_relationship_error", error=str(e))
            return False

    def close(self):
        if self.driver:
            self.driver.close()
