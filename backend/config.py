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

    # LLM (Phase 4+)
    llm_provider: str = "local"
    ollama_base_url: str = "http://host.docker.internal:11434"
    ollama_model: str = "qwen3:8b"
    embedding_model: str = "bge-m3"

    class Config:
        env_file = ".env.local"
        case_sensitive = False

@lru_cache()
def get_config() -> Settings:
    return Settings()
