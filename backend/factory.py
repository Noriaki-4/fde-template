"""Service Factory for Dependency Injection"""

from typing import Union
from backend.config import Settings
from backend.services.search import SearchService
from backend.services.graph import GraphService, Neo4jGraphService
from backend.services.rdf import RDFService, VirtuosoRDFService
from backend.services.agent import AgentService
from backend.services.llm import LLMService, OllamaLLMService
from backend.database.nosql.base import NoSQLRepository


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
        if config.llm_provider == "ollama":
            # Ollama: supports qwen, gemma, mistral, etc.
            return OllamaLLMService(
                config.ollama_base_url,
                config.llm_model,
            )
        elif config.llm_provider == "bedrock":
            from backend.services.bedrock import BedrockLLMService

            return BedrockLLMService(
                config.bedrock_model_id,
                config.aws_region,
            )
        return None

    @staticmethod
    def create_nosql_service(config: Settings) -> Union[NoSQLRepository, None]:
        """Create NoSQL service based on configuration"""
        if not config.nosql_enabled:
            return None

        if config.nosql_engine == "dynamodb":
            from backend.database.nosql.dynamodb import DynamoDBRepository

            return DynamoDBRepository(
                config.nosql_table_name,
                config.aws_region,
            )
        elif config.nosql_engine == "scylladb":
            from backend.database.nosql.scylladb import ScyllaDBRepository

            return ScyllaDBRepository(
                config.scylladb_endpoint,
                config.nosql_table_name,
            )
        return None
