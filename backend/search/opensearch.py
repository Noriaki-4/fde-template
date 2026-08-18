from opensearchpy import OpenSearch
from typing import List, Dict, Any
import structlog
from backend.config import get_config

logger = structlog.get_logger()

class OpenSearchClient:
    def __init__(self):
        config = get_config()
        if not config.opensearch_enabled:
            self.client = None
            return

        self.client = OpenSearch(
            hosts=[{"host": config.opensearch_url.replace("http://", ""), "port": 9200}],
            http_auth=("admin", "Passw0rd!"),
            use_ssl=False,
            verify_certs=False,
            ssl_show_warn=False,
        )
        self.index_name = "documents"

    def index_document(self, doc_id: str, title: str, content: str, metadata: dict = None) -> bool:
        if not self.client:
            return False
        try:
            self.client.index(
                index=self.index_name,
                id=doc_id,
                body={"title": title, "content": content, "metadata": metadata or {}}
            )
            self.client.indices.refresh(index=self.index_name)
            logger.info("document_indexed_opensearch", doc_id=doc_id)
            return True
        except Exception as e:
            logger.error("opensearch_index_error", error=str(e))
            return False

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            response = self.client.search(
                index=self.index_name,
                body={
                    "query": {"multi_match": {"query": query, "fields": ["title", "content"]}},
                    "size": limit
                }
            )
            return [hit["_source"] for hit in response.get("hits", {}).get("hits", [])]
        except Exception as e:
            logger.error("opensearch_search_error", error=str(e))
            return []

    def delete(self, doc_id: str) -> bool:
        if not self.client:
            return False
        try:
            self.client.delete(index=self.index_name, id=doc_id)
            self.client.indices.refresh(index=self.index_name)
            return True
        except Exception as e:
            logger.error("opensearch_delete_error", error=str(e))
            return False
