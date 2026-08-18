"""Graph Storage Service - S3/MinIO"""

from typing import Any
from minio import Minio
import io

from backend.graph.canonical.models import CanonicalGraph
from backend.graph.canonical.serializer import CanonicalGraphSerializer


class GraphStorageService:
    """Store canonical graphs to S3/MinIO"""

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str = "graph-storage",
        use_ssl: bool = False,
    ):
        self.endpoint = endpoint
        self.bucket = bucket
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=use_ssl,
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except Exception as e:
            print(f"Bucket creation warning: {e}")

    async def save_graph(self, graph_id: str, canonical: CanonicalGraph) -> bool:
        """Save canonical graph to S3"""
        try:
            nodes_jsonl, relations_jsonl = CanonicalGraphSerializer.to_jsonl(
                canonical
            )

            # Save nodes
            nodes_data = io.BytesIO(nodes_jsonl.encode())
            self.client.put_object(
                self.bucket,
                f"graphs/{graph_id}/nodes.jsonl",
                nodes_data,
                len(nodes_jsonl),
            )

            # Save relations
            relations_data = io.BytesIO(relations_jsonl.encode())
            self.client.put_object(
                self.bucket,
                f"graphs/{graph_id}/relations.jsonl",
                relations_data,
                len(relations_jsonl),
            )

            # Save metadata
            metadata = {
                "graph_id": graph_id,
                "node_count": len(canonical.nodes),
                "relation_count": len(canonical.relations),
            }
            import json

            metadata_data = io.BytesIO(json.dumps(metadata).encode())
            self.client.put_object(
                self.bucket,
                f"graphs/{graph_id}/metadata.json",
                metadata_data,
                len(json.dumps(metadata)),
            )

            return True
        except Exception as e:
            print(f"Error saving graph: {e}")
            return False

    async def load_graph(self, graph_id: str) -> CanonicalGraph | None:
        """Load canonical graph from S3"""
        try:
            # Load nodes
            nodes_response = self.client.get_object(
                self.bucket, f"graphs/{graph_id}/nodes.jsonl"
            )
            nodes_data = nodes_response.read().decode()

            # Load relations
            relations_response = self.client.get_object(
                self.bucket, f"graphs/{graph_id}/relations.jsonl"
            )
            relations_data = relations_response.read().decode()

            return CanonicalGraphSerializer.from_jsonl(nodes_data, relations_data)
        except Exception as e:
            print(f"Error loading graph: {e}")
            return None

    async def delete_graph(self, graph_id: str) -> bool:
        """Delete graph from S3"""
        try:
            self.client.remove_object(self.bucket, f"graphs/{graph_id}/nodes.jsonl")
            self.client.remove_object(
                self.bucket, f"graphs/{graph_id}/relations.jsonl"
            )
            self.client.remove_object(self.bucket, f"graphs/{graph_id}/metadata.json")
            return True
        except Exception as e:
            print(f"Error deleting graph: {e}")
            return False

    async def list_graphs(self) -> list[str]:
        """List all stored graphs"""
        try:
            graphs = set()
            objects = self.client.list_objects(self.bucket, prefix="graphs/")
            for obj in objects:
                path_parts = obj.object_name.split("/")
                if len(path_parts) >= 2:
                    graphs.add(path_parts[1])
            return sorted(list(graphs))
        except Exception:
            return []
