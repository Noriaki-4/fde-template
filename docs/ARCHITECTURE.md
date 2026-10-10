# Architecture Overview

FDE Template follows a modular, interface-first architecture supporting both local OSS and AWS managed services.

## Core Principles

1. **Interface-First**: Use standard interfaces (openCypher, SPARQL, S3 API, DynamoDB API) not product-specific APIs
2. **Local ↔ AWS Parity**: Identical application code via configuration switching
3. **Modular Capabilities**: Features ON/OFF per project without tight coupling
4. **Separation of Concerns**: Routes → Services → Repositories → Models

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│              Gradio UI / Streamlit UI (Frontend)         │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   FastAPI (Backend)                      │
├─────────────────────────────────────────────────────────┤
│  Routes (health, search, rag, graph, nosql,             │
│          opensearch, genu_chat)                          │
│  ↓                                                       │
│  Services (SearchService, GraphService, RDFService,     │
│            LLMService, RAGService, NoSQLRepository,      │
│            OpenSearchInterface)                           │
│  ↓                                                       │
│  Repositories (DocumentRepository)                       │
│  ↓                                                       │
│  Database Layer (SQLAlchemy ORM, Models)                │
└─────────────────────────────────────────────────────────┘
         ↓              ↓              ↓
    PostgreSQL      MinIO         OpenSearch/Neo4j/DynamoDB
    (Relational)  (Object)       (Search/Graph/NoSQL)
```

> Agent Runtime（`backend/agent/`, `backend/services/agent.py`）は実装のみで
> 上記のリクエストフローには組み込まれていない。詳細は [AGENTS.md](../AGENTS.md)。

## Layer Breakdown

### 1. Routes (`backend/api/routes/`)

HTTP entry points with FastAPI dependencies.

```python
@router.post("/search/")
async def search(query: SearchQuery, service: SearchService = Depends()):
    results = await service.search(query.text)
    return {"results": results}
```

**Responsibilities:**
- Parse HTTP requests
- Validate input
- Delegate to services
- Format responses

### 2. Services (`backend/services/`)

Most services follow an ABC + concrete-implementation pattern; the DB-backed
search service is the one exception (concrete class, constructed with a
per-request `Session`).

```python
class GraphService(ABC):
    @abstractmethod
    async def query(self, cypher: str, params: dict | None = None) -> list[dict]:
        pass

class Neo4jGraphService(GraphService):
    ...
```

**Services and their concrete implementations:**
- `SearchService` (`backend/services/search.py`) — concrete, DB-backed (Phase 1)
- `OpenSearchInterface` (ABC) → `OpenSearchService` (Phase 2)
- `GraphService` (ABC) → `Neo4jGraphService` (Phase 3)
- `RDFService` (ABC) → `VirtuosoRDFService` (Phase 3)
- `LLMService` (ABC) → `OllamaLLMService` / `BedrockLLMService` (Phase 4)
- `NoSQLRepository` (ABC) → `DynamoDBRepository` / `ScyllaDBRepository` (Phase 7)
- `RAGService` (`backend/services/rag.py`) — composes the above, no ABC
- `AgentService` (ABC) → `LocalAgentService` (Phase 4) — **implemented but not wired**, see [AGENTS.md](../AGENTS.md)

### 3. Repositories (`backend/repositories/`)

Data access abstraction using Repository pattern.

```python
class DocumentRepository(Repository[Document]):
    def find_by_title(self, title: str) -> Document | None:
        pass
    
    def search_by_content(self, query: str) -> list[Document]:
        pass
```

### 4. Models (`backend/database/models.py`)

SQLAlchemy ORM models defining schema.

```python
class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    metadata: Mapped[dict] = mapped_column(JSON)
```

## Data Flow

```
Request → Route → Service → Repository → Model → Database/Storage
                    ↓
                 Business Logic
                    ↓
Response ← Route ← Service ← Repository ← Database/Storage
```

## Configuration & Switching

Environment variables (`.env.local`, read by `backend/config.py`'s
`pydantic-settings` `Settings` class) control feature activation —
**not** `project.yaml`. `profiles/*.yaml` are reference templates only;
nothing in the app reads them automatically.

```bash
OPENSEARCH_ENABLED=true
OPENSEARCH_URL=http://opensearch:9200
```

Dependency Injection via FastAPI, following the pattern used for every
wired service (`graph`, `rdf`, `llm`, `nosql`, `opensearch`):

```python
# backend/api/routes/opensearch.py
async def get_opensearch_service(config=Depends(get_config)) -> OpenSearchInterface | None:
    from backend.api.main import get_opensearch_service as _get
    return _get()

@router.get("/health")
async def opensearch_health(service: OpenSearchInterface | None = Depends(get_opensearch_service)):
    ...
```

`ServiceFactory` (`backend/factory.py`) selects the implementation and is
called once at app startup (`backend/api/main.py`'s `startup_event`):

```python
@staticmethod
def create_opensearch_service(config: Settings) -> OpenSearchInterface | None:
    if not config.opensearch_enabled:
        return None
    return OpenSearchService(config.opensearch_url)
```

## Phase Architecture

### Phase 1: Core RAG
```
Gradio → FastAPI → PostgreSQL/MinIO
         Search Service (database-based)
```

### Phase 2: Full-Text Search
```
Phase 1 + OpenSearch
         Search Service (opensearch adapter)
```

### Phase 3: Knowledge Graphs
```
Phase 2 + Neo4j
         Graph Service (openCypher queries)
         Graph Repository
```

### Phase 4: LLM
```
Phase 3 + Ollama/Bedrock
         LLM Service (wired into Chat API)
         Agent Service (implemented, not wired — see AGENTS.md)
```

### Phase 5: AWS Deployment
```
Phase 4 → AWS CDK
         RDS PostgreSQL
         S3 Bucket
         OpenSearch Domain
         (CloudFormation stack)
```

### Phase 6: CLI & Profiles
```
fde init/up/down/deploy
Project profiles (rag-basic, graph-rag, agent-enabled)
Configuration management
```

## Storage Backends (S3 API Parity)

| Layer | Local | AWS | Interface |
|-------|-------|-----|-----------|
| Object Storage | MinIO | S3 | S3 API |
| Database | PostgreSQL | RDS | SQL |
| Search | OpenSearch | OpenSearch Domain | REST |
| Property Graph | Neo4j | Neptune | openCypher |
| RDF Graph | Virtuoso | Neptune | SPARQL |
| Cache | Redis | ElastiCache | Redis Protocol |

## Error Handling Strategy

```
Routes: HTTP error responses (400, 500, etc)
Services: Custom exceptions (SearchError, GraphError)
Repositories: Database exceptions wrapped
Models: Validation errors via Pydantic
```

## Testing Architecture

```
Unit Tests
├─ api/routes (mocked services)
├─ services (mocked repositories)
└─ repositories (in-memory/SQLite)

Integration Tests
├─ Database operations (PostgreSQL)
├─ Search operations (OpenSearch)
└─ Graph operations (Neo4j)

E2E Tests
└─ Full request lifecycle (API + UI)
```

## Security Layers

1. **Input Validation**: Pydantic schemas at routes
2. **Authentication**: Token-based (JWT, API keys)
3. **Authorization**: Permission checks in services
4. **Data Protection**: Encryption for sensitive fields
5. **Audit Logging**: Structlog for compliance

## Performance Considerations

- Connection pooling (SQLAlchemy)
- Caching layers (Redis)
- Async/await throughout
- Batch indexing (OpenSearch)
- Query pagination (databases)

## Extensibility Points

1. Add new Service implementations
2. Add new Repository adapters
3. Add new Routes
4. Add new Models/Schemas
5. Add new Storage backends (via S3/DynamoDB APIs)
6. Add batch jobs / pipelines (`backend/jobs/definitions/`, `backend/jobs/pipelines/` — see [JOBS.md](JOBS.md), ADR 004)
