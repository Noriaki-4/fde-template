"""Service Factory for Dependency Injection"""

from typing import Union

from backend.config import Settings
from backend.database.nosql.base import NoSQLRepository
from backend.jobs.context import SessionFactory
from backend.jobs.launcher import JobLauncher
from backend.services.graph import GraphService, Neo4jGraphService
from backend.services.llm import LLMService, OllamaLLMService
from backend.services.opensearch import OpenSearchInterface, OpenSearchService
from backend.services.rdf import RDFService, VirtuosoRDFService
from backend.storage.object_store import ObjectStore


class ServiceFactory:
    """Factory for creating service instances"""

    @staticmethod
    def create_graph_service(config: Settings) -> Union[GraphService, None]:
        """Create property graph service based on configuration"""
        if not config.graph_enabled:
            return None

        if config.graph_engine == "neo4j":
            return Neo4jGraphService(
                config.neo4j_uri,
                config.neo4j_user,
                config.neo4j_password,
            )
        return None

    @staticmethod
    def create_rdf_service(config: Settings) -> Union[RDFService, None]:
        """Create RDF graph service based on configuration"""
        if not config.rdf_enabled:
            return None

        if config.rdf_engine == "virtuoso":
            return VirtuosoRDFService(config.rdf_sparql_endpoint)
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

    @staticmethod
    def create_object_store(config: Settings) -> ObjectStore:
        """S3 API object store (MinIO locally, S3 on AWS) — used for job artifacts"""
        from backend.storage.object_store import S3ObjectStore

        return S3ObjectStore.from_config(config)

    @staticmethod
    def create_job_launcher(config: Settings, session_factory: SessionFactory) -> JobLauncher:
        """Job launcher: local subprocess or ECS RunTask (adr/004-job-execution.md)"""
        if config.job_launcher == "local":
            from backend.jobs.launcher import LocalJobLauncher

            return LocalJobLauncher(session_factory)
        if config.job_launcher == "ecs":
            from backend.jobs.aws import EcsJobLauncher

            return EcsJobLauncher.from_config(config, session_factory)
        raise ValueError(f"Unknown job_launcher: {config.job_launcher!r} (local | ecs)")

    @staticmethod
    def create_opensearch_service(config: Settings) -> Union[OpenSearchInterface, None]:
        """Create OpenSearch service based on configuration"""
        if not config.opensearch_enabled:
            return None

        return OpenSearchService(config.opensearch_url)
