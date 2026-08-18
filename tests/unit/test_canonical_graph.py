"""Tests for Canonical Graph Format"""

import pytest

from backend.graph.canonical.models import CanonicalNode, CanonicalRelation, CanonicalGraph
from backend.graph.canonical.serializer import CanonicalGraphSerializer
from backend.graph.canonical.transformer import GraphTransformer


@pytest.mark.unit
class TestCanonicalGraph:
    def test_canonical_node_creation(self):
        node = CanonicalNode(
            id="node1",
            label="TestNode",
            properties={"type": "entity"},
        )
        assert node.id == "node1"
        assert node.label == "TestNode"
        assert node.properties["type"] == "entity"

    def test_canonical_relation_creation(self):
        rel = CanonicalRelation(
            source="node1",
            target="node2",
            relation_type="CONNECTS_TO",
        )
        assert rel.source == "node1"
        assert rel.target == "node2"
        assert rel.relation_type == "CONNECTS_TO"

    def test_canonical_graph_add_node(self):
        graph = CanonicalGraph()
        node = CanonicalNode(id="n1", label="N1")
        graph.add_node(node)

        assert len(graph.nodes) == 1
        assert graph.nodes[0].id == "n1"

    def test_canonical_graph_add_relation(self):
        graph = CanonicalGraph()
        rel = CanonicalRelation(
            source="n1", target="n2", relation_type="REL"
        )
        graph.add_relation(rel)

        assert len(graph.relations) == 1
        assert graph.relations[0].relation_type == "REL"

    def test_node_to_dict(self):
        node = CanonicalNode(
            id="node1",
            label="TestNode",
            properties={"type": "entity"},
        )
        node_dict = node.to_dict()

        assert node_dict["id"] == "node1"
        assert node_dict["label"] == "TestNode"
        assert node_dict["properties"]["type"] == "entity"

    def test_canonical_serializer(self):
        graph = CanonicalGraph()
        graph.add_node(CanonicalNode(id="n1", label="N1"))
        graph.add_node(CanonicalNode(id="n2", label="N2"))
        graph.add_relation(
            CanonicalRelation(
                source="n1", target="n2", relation_type="REL"
            )
        )

        nodes_jsonl, relations_jsonl = CanonicalGraphSerializer.to_jsonl(graph)

        assert "n1" in nodes_jsonl
        assert "n2" in nodes_jsonl
        assert "REL" in relations_jsonl

    def test_canonical_deserializer(self):
        original_graph = CanonicalGraph()
        original_graph.add_node(CanonicalNode(id="n1", label="N1"))
        original_graph.add_node(CanonicalNode(id="n2", label="N2"))
        original_graph.add_relation(
            CanonicalRelation(
                source="n1", target="n2", relation_type="REL"
            )
        )

        nodes_jsonl, relations_jsonl = CanonicalGraphSerializer.to_jsonl(
            original_graph
        )
        loaded_graph = CanonicalGraphSerializer.from_jsonl(
            nodes_jsonl, relations_jsonl
        )

        assert len(loaded_graph.nodes) == 2
        assert len(loaded_graph.relations) == 1
        assert loaded_graph.relations[0].relation_type == "REL"

    def test_neo4j_to_canonical(self):
        neo4j_nodes = [
            {"id": "n1", "label": "Node1", "properties": {"type": "entity"}},
            {"id": "n2", "label": "Node2", "properties": {"type": "entity"}},
        ]
        neo4j_relations = [
            {
                "source": "n1",
                "target": "n2",
                "relation": "CONNECTS",
                "properties": {},
            }
        ]

        canonical = GraphTransformer.neo4j_to_canonical(
            neo4j_nodes, neo4j_relations
        )

        assert len(canonical.nodes) == 2
        assert len(canonical.relations) == 1
        assert canonical.nodes[0].label == "Node1"
