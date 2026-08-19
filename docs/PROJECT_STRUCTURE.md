# Project Structure

Complete file tree and documentation for FDE Template.

## Overview

```
fde-template/
├── README.md                          # Index / navigation (points into docs/)
├── AGENTS.md                          # Agent/LLM reference (CLAUDE.md symlinks here)
├── Makefile                           # Common commands
├── setup.py                           # Python package setup
├── pyproject.toml                     # Dependencies & config
│
├── backend/                           # FastAPI backend
│   ├── Dockerfile
│   ├── api/
│   │   ├── main.py                    # FastAPI app, service wiring, router registration
│   │   └── routes/
│   │       ├── health.py              # Health check endpoint
│   │       ├── search.py              # DB-backed document search (Phase 1)
│   │       ├── rag.py                 # Unified RAG: search + graph + rdf
│   │       ├── graph.py               # openCypher / SPARQL queries (Phase 3, gated by RDF_ENABLED)
│   │       ├── nosql.py               # NoSQL CRUD (Phase 7, gated by NOSQL_ENABLED)
│   │       ├── opensearch.py          # OpenSearch index/search (Phase 2, gated by OPENSEARCH_ENABLED)
│   │       └── genu_chat.py           # GenU-compatible chat API (Phase 9), calls LLM service
│   │
│   ├── config.py                      # Settings (pydantic-settings, reads .env.local)
│   ├── factory.py                     # ServiceFactory — creates service instances from config
│   │
│   ├── database/
│   │   ├── db.py                      # SQLAlchemy session management
│   │   ├── models.py                  # SQLAlchemy ORM models (Document, SearchIndex, ProjectConfig)
│   │   └── nosql/
│   │       ├── base.py                # NoSQLRepository ABC
│   │       ├── dynamodb.py            # DynamoDBRepository (boto3)
│   │       └── scylladb.py            # ScyllaDBRepository (boto3 via Alternator API)
│   │
│   ├── repositories/
│   │   ├── base.py                    # Generic repository base class
│   │   └── document.py                # Document repository (SQLAlchemy)
│   │
│   ├── services/
│   │   ├── search.py                  # SearchService — DB-backed document search (Phase 1)
│   │   ├── opensearch.py              # OpenSearchInterface (ABC) + OpenSearchService (Phase 2)
│   │   ├── graph.py                   # GraphService (ABC) + Neo4jGraphService (Phase 3)
│   │   ├── rdf.py                     # RDFService (ABC) + VirtuosoRDFService (Phase 3)
│   │   ├── rag.py                     # RAGService — composes search + graph + rdf
│   │   ├── llm.py                     # LLMService (ABC) + OllamaLLMService (Phase 4)
│   │   ├── bedrock.py                 # BedrockLLMService (Phase 4/7, AWS)
│   │   └── agent.py                   # AgentService (ABC) + LocalAgentService — NOT wired into main.py
│   │
│   ├── agent/                         # Agent Runtime — implemented but NOT wired (see AGENTS.md)
│   │   ├── runtime.py                 # AgentRuntime (ABC) + LocalAgentRuntime
│   │   └── agentcore.py               # AgentCoreRuntime (AWS bedrock-agentcore)
│   │
│   ├── graph/
│   │   ├── neo4j_client.py            # Standalone Neo4j client — unused duplicate of Neo4jGraphService
│   │   └── canonical/                 # Canonical graph model (Phase 8) — used by graph_store.py only
│   │       ├── models.py              # CanonicalNode / CanonicalRelation / CanonicalGraph dataclasses
│   │       ├── transformer.py         # Neo4j / RDF → canonical format
│   │       └── serializer.py          # Canonical graph (de)serialization
│   │
│   └── storage/
│       └── graph_store.py             # GraphStorageService — persists canonical graphs to MinIO/S3, NOT wired into main.py
│
├── frontend/
│   ├── gradio/
│   │   ├── Dockerfile
│   │   └── app.py                     # Gradio UI (recommended)
│   └── streamlit/
│       ├── Dockerfile
│       └── app.py                     # Streamlit UI (alternative)
│
├── cli/                                # CLI (Phase 6)
│   └── fde_cli.py                     # CLI commands (init, up, down, validate, deploy)
│
├── cdk/                                # AWS CDK (Phase 5)
│   ├── package.json
│   ├── lib/
│   │   └── fde_stack.py               # CDK stack definition
│   └── bin/
│       └── app.ts                     # CDK app entry
│
├── profiles/                           # Config templates (not auto-loaded by the app — see below)
│   ├── rag-basic.yaml
│   ├── graph-rag.yaml
│   ├── agent-enabled.yaml
│   ├── aws-production.yaml
│   ├── hybrid-bedrock-local.yaml
│   └── gemma-local.yaml
│
├── scripts/
│   ├── init_db.py                     # Database initialization
│   ├── seed_documents.py              # Sample data seeding
│   └── seed_graph.py                  # Graph data seeding
│
├── tests/
│   ├── conftest.py                    # Shared fixtures (db, client); sets NOSQL/OPENSEARCH_ENABLED=true
│   ├── unit/
│   │   ├── test_api_health.py
│   │   ├── test_api_search.py
│   │   ├── test_api_rag.py
│   │   ├── test_api_nosql.py
│   │   ├── test_api_opensearch.py
│   │   ├── test_genu_chat.py          # Mocks the LLM dependency
│   │   └── test_canonical_graph.py    # Tests canonical graph dataclasses/transformer/serializer only
│   │
│   └── integration/
│       └── test_database.py
│
├── infra/
│   └── docker-compose.yml             # Postgres, MinIO, backend, gradio, streamlit, opensearch*, neo4j*, virtuoso*, scylladb*
│                                       # (* behind compose profiles: with-search, with-graph, with-rdf, with-nosql)
│
├── docs/                               # All documentation (see docs/README.md for the index)
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── SETUP.md
│   ├── USAGE.md
│   ├── ARCHITECTURE.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── PROJECT_STRUCTURE.md           # This file
│   ├── RUNBOOK.md
│   └── requirements/
│
├── adr/                                # Architecture Decision Records
│   ├── 001-interface-first-architecture.md
│   └── 002-local-aws-parity.md
│
├── .env.example                        # Environment template
├── .github/workflows/
│   ├── test.yml
│   └── deploy.yml
│
└── LICENSE
```

**Note:** `AGENTS.md` and `README.md` live at the repository root; every other
`.md` document lives under `docs/`. `CLAUDE.md` at the root is a symlink to
`AGENTS.md`.

## File Descriptions

### Documentation Files

| File | Location | Purpose |
|------|----------|---------|
| `README.md` | root | Index / navigation into `docs/` |
| `AGENTS.md` | root | Agent/LLM integration reference — what's wired vs. orphaned |
| `docs/QUICKSTART.md` | docs/ | Get started in 5 minutes |
| `docs/SETUP.md` | docs/ | Detailed installation |
| `docs/USAGE.md` | docs/ | How to use this template for a new project |
| `docs/ARCHITECTURE.md` | docs/ | System design & component breakdown |
| `docs/IMPLEMENTATION_PLAN.md` | docs/ | Phase 1-9 roadmap with details |
| `docs/RUNBOOK.md` | docs/ | Operations procedures & troubleshooting |
| `docs/PROJECT_STRUCTURE.md` | docs/ | This file — project layout |

### Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python dependencies & build config (single source of truth — no `requirements.txt`) |
| `setup.py` | Package installation config |
| `.env.example` | Environment variables template (read via `.env.local`, see `backend/config.py`) |

### Backend (`backend/`)

| Module | Phase | Wired? | Purpose |
|--------|-------|--------|---------|
| `api/main.py` | 1 | — | FastAPI app setup, service instantiation, router registration |
| `api/routes/health.py`, `search.py` | 1 | Yes (always on) | Core health/search endpoints |
| `api/routes/rag.py` | — | Yes (always on) | Unified search across search+graph+rdf |
| `api/routes/graph.py` | 3 | Yes (if `RDF_ENABLED`) | openCypher / SPARQL endpoints |
| `api/routes/nosql.py` | 7 | Yes (if `NOSQL_ENABLED`) | NoSQL CRUD endpoints |
| `api/routes/opensearch.py` | 2 | Yes (if `OPENSEARCH_ENABLED`) | OpenSearch index/search endpoints |
| `api/routes/genu_chat.py` | 9 | Yes (always on) | Chat API, calls the real LLM service |
| `factory.py` | — | — | `ServiceFactory.create_*` — graph, rdf, llm, nosql, opensearch |
| `services/agent.py`, `agent/runtime.py`, `agent/agentcore.py` | 4/8 | **No** | Implemented, no factory method, no route — see AGENTS.md |
| `storage/graph_store.py`, `graph/canonical/*` | 8 | **No** | Implemented, no factory method, no route |
| `graph/neo4j_client.py` | 3 | **No** | Unused duplicate of `services/graph.py`'s `Neo4jGraphService` |

### Frontend (`frontend/`)

| File | Purpose |
|------|---------|
| `gradio/app.py`, `gradio/Dockerfile` | Gradio UI (recommended default) |
| `streamlit/app.py`, `streamlit/Dockerfile` | Streamlit UI (alternative) |

### Infrastructure

| File | Purpose |
|------|---------|
| `infra/docker-compose.yml` | Local container orchestration; optional services behind compose `profiles` |
| `cdk/lib/fde_stack.py` | AWS infrastructure as code (Phase 5) |

### CLI & Profiles (Phase 6)

| File | Purpose |
|------|---------|
| `cli/fde_cli.py` | CLI commands (`init`, `up`, `down`, `validate`, `deploy`) |
| `profiles/*.yaml` | Reference configuration templates. **Not auto-loaded**: `cli/fde_cli.py init` writes a hardcoded `project.yaml`, it does not read these files; `backend/config.py` reads only environment variables (`.env.local`), not `project.yaml`. Use a profile's values as a source to copy into `.env.local`. |

### Testing

| File | Type | Notes |
|------|------|-------|
| `tests/conftest.py` | Setup | `client`/`db` fixtures; sets `NOSQL_ENABLED`/`OPENSEARCH_ENABLED=true` before app import so those routers register during tests |
| `tests/unit/test_api_health.py`, `test_api_search.py` | Unit | Core endpoints |
| `tests/unit/test_api_rag.py`, `test_api_nosql.py`, `test_api_opensearch.py` | Unit | Mock the underlying service via `app.dependency_overrides` |
| `tests/unit/test_genu_chat.py` | Unit | Mocks the LLM dependency with a `FakeLLMService` |
| `tests/unit/test_canonical_graph.py` | Unit | Tests canonical graph dataclasses only — not the storage/API layer |
| `tests/integration/test_database.py` | Integration | Database layer |

### Scripts

| File | Purpose |
|------|---------|
| `scripts/init_db.py` | Create/reset database schema |
| `scripts/seed_documents.py` | Load sample documents |
| `scripts/seed_graph.py` | Load sample graph data |

### CI/CD

| File | Purpose |
|------|---------|
| `.github/workflows/test.yml` | Test & lint on every PR |
| `.github/workflows/deploy.yml` | Deploy to AWS on main branch |

## Adding New Features

1. **Add a model**: `backend/database/models.py`
2. **Add a repository**: `backend/repositories/new_repo.py`
3. **Add a service**: `backend/services/new_service.py`
4. **Add a factory method**: `backend/factory.py` — `ServiceFactory.create_*`
5. **Wire it into `backend/api/main.py`**: global variable, getter function, startup-event instantiation, conditional or unconditional router registration
6. **Add routes**: `backend/api/routes/new_route.py`
7. **Add tests**: `tests/unit/test_api_new.py`, overriding the route's dependency getter with a fake

This is the exact pattern `graph`/`rdf`/`llm`/`nosql`/`opensearch`/`rag` all follow — a service implemented but skipping step 5 is the most common way a feature ends up orphaned (see AGENTS.md for currently-orphaned examples).

## Naming Conventions

- **Classes**: PascalCase (`DocumentRepository`, `SearchService`)
- **Functions**: snake_case (`get_document`, `search_index`)
- **Files**: snake_case (`document.py`, `search.py`)
- **Models**: Singular (`Document`, not `Documents`)
- **Databases**: plural (`documents` table)

## Code Organization Principles

1. **Single Responsibility**: One class = one job
2. **Dependency Injection**: FastAPI `Depends()`
3. **Repository Pattern**: Encapsulate data access
4. **Service Layer**: Business logic separation
5. **Async/Await**: Throughout the stack
