from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    app_name: str = "FDE Template"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fde_poc"

    # Storage
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "knowledge-root"
    minio_use_ssl: bool = False

    # Search (Phase 2+)
    opensearch_url: str = "http://localhost:9200"
    opensearch_enabled: bool = False

    # Graph (Phase 3+)
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_enabled: bool = False

    # RDF (Phase 3+)
    rdf_model: str = "property_graph"  # property_graph | rdf
    rdf_engine: str = "neo4j"  # neo4j | virtuoso
    rdf_sparql_endpoint: str = "http://localhost:8890/sparql"
    rdf_enabled: bool = False

    # NoSQL (Phase 7+)
    nosql_enabled: bool = False
    nosql_engine: str = "dynamodb"  # dynamodb | scylladb
    nosql_table_name: str = "fde-data"
    scylladb_endpoint: str = "http://localhost:8000"
    aws_region: str = "ap-northeast-1"

    # LLM (Phase 4+)
    llm_provider: str = "ollama"  # ollama (qwen/gemma/mistral) | bedrock
    ollama_base_url: str = "http://host.docker.internal:11434"
    llm_model: str = "qwen:7b"  # ollama models: qwen:7b, gemma:4-e4b, mistral:7b, etc.
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    embedding_model: str = "bge-m3"

    class Config:
        env_file = ".env.local"
        case_sensitive = False

@lru_cache()
def get_config() -> Settings:
    return Settings()
