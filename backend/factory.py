"""Service Factory for Dependency Injection"""

from typing import Union
from backend.config import Settings
from backend.services.search import SearchService
from backend.services.graph import GraphService, Neo4jGraphService
from backend.services.rdf import RDFService, VirtuosoRDFService
from backend.services.agent import AgentService
from backend.services.llm import LLMService, OllamaLLMService


class ServiceFactory:
    """Factory for creating service instances"""

    @staticmethod
    def create_graph_service(config: Settings) -> Union[GraphService, None]:
        """Create graph service based on configuration"""
        if not config.rdf_enabled:
            return None

        if config.rdf_model == "property_graph":
            if config.rdf_engine == "neo4j":
                return Neo4jGraphService(
                    config.neo4j_uri,
                    config.neo4j_user,
                    config.neo4j_password,
                )
            return None

        return None

    @staticmethod
    def create_rdf_service(config: Settings) -> Union[RDFService, None]:
        """Create RDF service based on configuration"""
        if not config.rdf_enabled:
            return None

        if config.rdf_model == "rdf":
            if config.rdf_engine == "virtuoso":
                return VirtuosoRDFService(config.rdf_sparql_endpoint)
            return None

        return None

    @staticmethod
    def create_llm_service(config: Settings) -> Union[LLMService, None]:
        """Create LLM service based on configuration"""
        if config.llm_provider == "local":
            return OllamaLLMService(
                config.ollama_base_url,
                config.ollama_model,
            )
        return None
