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
│                    Gradio UI (Frontend)                 │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                   FastAPI (Backend)                      │
├─────────────────────────────────────────────────────────┤
│  Routes (health.py, search.py, ...)                     │
│  ↓                                                       │
│  Services (SearchService, GraphService, AgentService)  │
│  ↓                                                       │
│  Repositories (DocumentRepository, GraphRepository)    │
│  ↓                                                       │
│  Database Layer (SQLAlchemy ORM, Models)               │
└─────────────────────────────────────────────────────────┘
         ↓              ↓              ↓
    PostgreSQL      MinIO         OpenSearch/Neo4j
    (Relational)  (Object)       (Search/Graph)
```

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

Business logic encapsulation with abstract interfaces.

```python
class SearchService(ABC):
    @abstractmethod
    async def search(self, query: str) -> list[Document]:
        pass
```

**Implementations:**
- DatabaseSearchService (Phase 1)
- OpenSearchService (Phase 2)
- GraphQueryService (Phase 3)
- AgentService (Phase 4)

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

`project.yaml` controls feature activation:

```yaml
search:
  enabled: true
  engine: opensearch
```

Dependency Injection via FastAPI:

```python
@app.get("/search/")
async def search(service: SearchService = Depends(get_search_service)):
    # Service implementation is swapped at runtime
    return await service.search(...)
```

Factory pattern selects implementation:

```python
def get_search_service(config: Settings) -> SearchService:
    if config.search_enabled:
        if config.search_engine == "opensearch":
            return OpenSearchService(config.opensearch_url)
        return DatabaseSearchService()
    return None
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

### Phase 4: Agent/LLM
```
Phase 3 + Ollama/Claude
         Agent Service
         LLM Service
         Redis Cache
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
| Graph | Neo4j | Neptune | openCypher/SPARQL |
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
