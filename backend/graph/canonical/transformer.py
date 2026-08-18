"""Graph Transformer - Convert to/from Canonical Format"""

from typing import Any

from backend.graph.canonical.models import CanonicalNode, CanonicalRelation, CanonicalGraph


class GraphTransformer:
    """Transform between different graph representations"""

    @staticmethod
    def neo4j_to_canonical(neo4j_nodes: list[dict], neo4j_relations: list[dict]) -> CanonicalGraph:
        """Convert Neo4j Property Graph to Canonical format"""
        canonical = CanonicalGraph()

        # Convert nodes
        for node in neo4j_nodes:
            canonical_node = CanonicalNode(
                id=node.get("id"),
                label=node.get("label"),
                properties=node.get("properties", {}),
                metadata={"source": "neo4j"},
            )
            canonical.add_node(canonical_node)

        # Convert relations
        for rel in neo4j_relations:
            canonical_rel = CanonicalRelation(
                source=rel.get("source"),
                target=rel.get("target"),
                relation_type=rel.get("relation"),
                properties=rel.get("properties", {}),
                metadata={"source": "neo4j"},
            )
            canonical.add_relation(canonical_rel)

        return canonical

    @staticmethod
    def rdf_to_canonical(rdf_triples: list[tuple[str, str, str]]) -> CanonicalGraph:
        """Convert RDF triples to Canonical format"""
        canonical = CanonicalGraph()

        # Create nodes from subjects and objects
        subjects = set()
        objects = set()

        for subject, predicate, obj in rdf_triples:
            subjects.add(subject)
            objects.add(obj)

        # Add all URIs as nodes
        for uri in subjects | objects:
            node = CanonicalNode(
                id=uri,
                label=uri.split("/")[-1],
                properties={"uri": uri},
                metadata={"source": "rdf"},
            )
            canonical.add_node(node)

        # Add relations from predicates
        for subject, predicate, obj in rdf_triples:
            rel = CanonicalRelation(
                source=subject,
                target=obj,
                relation_type=predicate.split("/")[-1],
                properties={"predicate": predicate},
                metadata={"source": "rdf"},
            )
            canonical.add_relation(rel)

        return canonical

    @staticmethod
    def canonical_to_neo4j(canonical: CanonicalGraph) -> tuple[list[dict], list[dict]]:
        """Convert Canonical format to Neo4j queries"""
        nodes = []
        relations = []

        for node in canonical.nodes:
            nodes.append(
                {
                    "id": node.id,
                    "label": node.label,
                    "properties": node.properties,
                }
            )

        for rel in canonical.relations:
            relations.append(
                {
                    "source": rel.source,
                    "target": rel.target,
                    "relation": rel.relation_type,
                    "properties": rel.properties,
                }
            )

        return nodes, relations

    @staticmethod
    def canonical_to_sparql(canonical: CanonicalGraph) -> list[tuple[str, str, str]]:
        """Convert Canonical format to RDF triples"""
        triples = []

        for rel in canonical.relations:
            # Create RDF triple: subject predicate object
            subject_uri = canonical._get_node_uri(rel.source)
            predicate_uri = f"http://schema.fde/ns/{rel.relation_type}"
            object_uri = canonical._get_node_uri(rel.target)

            triples.append((subject_uri, predicate_uri, object_uri))

        return triples

    @staticmethod
    def _get_node_uri(canonical: CanonicalGraph, node_id: str) -> str:
        """Get or generate URI for node"""
        for node in canonical.nodes:
            if node.id == node_id:
                if "uri" in node.properties:
                    return node.properties["uri"]
                return f"http://schema.fde/resource/{node_id}"
        return f"http://schema.fde/resource/{node_id}"
