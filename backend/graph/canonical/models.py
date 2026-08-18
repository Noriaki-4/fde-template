"""Canonical Graph Format Models"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonicalNode:
    """Canonical node representation"""

    id: str
    label: str
    properties: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "properties": self.properties,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanonicalNode":
        return cls(
            id=data.get("id"),
            label=data.get("label"),
            properties=data.get("properties", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CanonicalRelation:
    """Canonical relationship representation"""

    source: str
    target: str
    relation_type: str
    properties: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "properties": self.properties,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CanonicalRelation":
        return cls(
            source=data.get("source"),
            target=data.get("target"),
            relation_type=data.get("relation_type"),
            properties=data.get("properties", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class CanonicalGraph:
    """Canonical graph container"""

    nodes: list[CanonicalNode] = field(default_factory=list)
    relations: list[CanonicalRelation] = field(default_factory=list)

    def add_node(self, node: CanonicalNode) -> None:
        """Add node to graph"""
        if not any(n.id == node.id for n in self.nodes):
            self.nodes.append(node)

    def add_relation(self, relation: CanonicalRelation) -> None:
        """Add relationship to graph"""
        if not any(
            r.source == relation.source and r.target == relation.target
            for r in self.relations
        ):
            self.relations.append(relation)

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "relations": [r.to_dict() for r in self.relations],
        }
