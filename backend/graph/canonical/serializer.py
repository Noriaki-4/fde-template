"""Canonical Graph Serialization (JSONL)"""

import json
from typing import Any, AsyncIterator

from backend.graph.canonical.models import CanonicalNode, CanonicalRelation, CanonicalGraph


class CanonicalGraphSerializer:
    """Serialize/deserialize Canonical graphs to JSONL"""

    @staticmethod
    def to_jsonl(canonical: CanonicalGraph) -> tuple[str, str]:
        """Convert to JSONL format (nodes.jsonl, relations.jsonl)"""
        nodes_jsonl = "\n".join(
            json.dumps(node.to_dict()) for node in canonical.nodes
        )

        relations_jsonl = "\n".join(
            json.dumps(rel.to_dict()) for rel in canonical.relations
        )

        return nodes_jsonl, relations_jsonl

    @staticmethod
    def from_jsonl(nodes_jsonl: str, relations_jsonl: str) -> CanonicalGraph:
        """Load from JSONL format"""
        canonical = CanonicalGraph()

        # Load nodes
        for line in nodes_jsonl.strip().split("\n"):
            if line:
                data = json.loads(line)
                node = CanonicalNode.from_dict(data)
                canonical.add_node(node)

        # Load relations
        for line in relations_jsonl.strip().split("\n"):
            if line:
                data = json.loads(line)
                rel = CanonicalRelation.from_dict(data)
                canonical.add_relation(rel)

        return canonical

    @staticmethod
    async def stream_nodes(nodes: list[CanonicalNode]) -> AsyncIterator[str]:
        """Stream nodes as JSONL"""
        for node in nodes:
            yield json.dumps(node.to_dict()) + "\n"

    @staticmethod
    async def stream_relations(relations: list[CanonicalRelation]) -> AsyncIterator[str]:
        """Stream relations as JSONL"""
        for rel in relations:
            yield json.dumps(rel.to_dict()) + "\n"
