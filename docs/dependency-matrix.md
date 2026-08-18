# Dependency Matrix

Version management across all phases with compatibility matrix.

## Python & Core

| Package | Version | Min Python | Phase | Notes |
|---------|---------|-----------|-------|-------|
| Python | 3.11+ | - | 1 | LTS support until 2027-10 |
| FastAPI | 0.115.6 | 3.8 | 1 | ASGI web framework |
| Uvicorn | 0.34.0 | 3.8 | 1 | ASGI server |
| Pydantic | 2.10.4 | 3.8 | 1 | Data validation |

## Database & Storage

| Package | Version | Min Python | Phase | Type | Notes |
|---------|---------|-----------|-------|------|-------|
| psycopg | 3.20.1 | 3.8 | 1 | Driver | PostgreSQL 16 binary |
| SQLAlchemy | 2.1.1 | 3.8 | 1 | ORM | Async support |
| minio | 7.2.13 | 3.8 | 1 | SDK | S3-compatible |
| boto3 | 1.28.85 | 3.8 | 1 | SDK | AWS SDK |

## Search & Graph (Phase 2-3)

| Package | Version | Min Python | Phase | Type | Notes |
|---------|---------|-----------|-------|------|-------|
| opensearch-py | 2.6.0 | 3.8 | 2 | Client | Vector search |
| neo4j | 5.27.0 | 3.8 | 3 | Driver | Async driver |

## LLM & Agent (Phase 4)

| Package | Version | Min Python | Phase | Type | Notes |
|---------|---------|-----------|-------|------|-------|
| ollama | 0.4.4 | 3.8 | 4 | SDK | Local LLM |
| anthropic | 0.42.0 | 3.8 | 4 | SDK | Claude API |
| langgraph | 0.1.46 | 3.9 | 4 | Framework | Agent orchestration |
| langchain-core | 0.1.52 | 3.9 | 4 | Framework | Components |

## CLI & Utils (Phase 6)

| Package | Version | Min Python | Phase | Type | Notes |
|---------|---------|-----------|-------|------|-------|
| click | 8.1.8 | 3.8 | 6 | CLI | Command framework |
| pyyaml | 6.0.2 | 3.8 | 6 | Utils | Config parsing |
| structlog | 24.4.0 | 3.8 | 1 | Logging | Structured logging |

## Development

| Package | Version | Min Python | Type | Notes |
|---------|---------|-----------|------|-------|
| pytest | 8.3.2 | 3.8 | Testing | Test runner |
| pytest-asyncio | 0.24.0 | 3.8 | Testing | Async support |
| pytest-cov | 5.0.0 | 3.8 | Testing | Coverage |
| black | 24.10.0 | 3.8 | Formatting | Code formatter |
| ruff | 0.8.2 | 3.7 | Linting | Fast linter |
| mypy | 1.14.1 | 3.8 | Type checking | Static type checker |

## AWS CDK (Phase 5)

| Package | Version | Min Node.js | Type | Notes |
|---------|---------|------------|------|-------|
| aws-cdk-lib | 2.165.0 | 18 | IaC | Infrastructure |
| constructs | 10.4.2 | 18 | IaC | CDK components |
| typescript | 5.6.2 | 18 | Language | TypeScript |

## Docker Versions

| Service | Image | Version | Notes |
|---------|-------|---------|-------|
| PostgreSQL | postgres | 16-alpine | Relational DB |
| MinIO | minio/minio | latest | Object storage |
| FastAPI | python | 3.11-slim | Backend runtime |
| Gradio | python | 3.11-slim | Frontend runtime |
| OpenSearch | opensearchproject/opensearch | 2.19 | Search engine |
| Neo4j | neo4j | 5.27 | Graph database |
| Ollama | ollama/ollama | latest | Local LLM |

## Compatibility Notes

### PostgreSQL 16 + SQLAlchemy 2.1.1
- Requires psycopg 3.x (binary variant)
- Async context manager support
- No deprecated dialect API

### Neo4j 5.27 + neo4j 5.27.0 Driver
- Async driver fully supported
- Compatible with openCypher 9
- Session pooling enabled

### OpenSearch 2.19 + opensearch-py 2.6.0
- Vector search (dense_vector type)
- Semantic search capabilities
- Bulk indexing optimized

### Ollama + anthropic SDK
- Local LLM fallback
- Anthropic for prod
- Configurable via LLM provider

## Phase Dependency Graph

```
Phase 1 (Core)
├─ FastAPI
├─ Pydantic
├─ SQLAlchemy
└─ psycopg

Phase 2 (Search)
├─ Phase 1 +
└─ opensearch-py

Phase 3 (Graph)
├─ Phase 2 +
└─ neo4j

Phase 4 (Agent/LLM)
├─ Phase 3 +
├─ ollama/anthropic
└─ langgraph/langchain

Phase 5 (AWS CDK)
├─ aws-cdk-lib
├─ constructs
└─ typescript

Phase 6 (CLI)
├─ Phase 1 +
├─ click
├─ pyyaml
└─ (all phases via import)
```

## Version Update Policy

- **Patch updates (x.y.Z)**: Auto-update (bug fixes, security)
- **Minor updates (x.Y.z)**: Quarterly review (features)
- **Major updates (X.y.z)**: Annual review (breaking changes)
- **End-of-life Python**: Drop support within 2 years of Python EOL

## Security Scanning

Run regularly:
```bash
uv pip audit
pip-audit
bandit -r backend/
```

## Testing Across Versions

- Python 3.11 (primary)
- Optional: Python 3.12 (upcoming)
- Minimum: Python 3.11 (LTS)
