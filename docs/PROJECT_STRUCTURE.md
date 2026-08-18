# Project Structure

Complete file tree and documentation for FDE Template.

## Overview

```
fde-template/
├── README.md                          # Main documentation
├── QUICKSTART.md                      # Quick start guide
├── ARCHITECTURE.md                    # Architecture overview
├── IMPLEMENTATION_PLAN.md             # Phase 1-6 roadmap
├── RUNBOOK.md                         # Operational procedures
├── AGENTS.md                          # Agent/LLM reference
├── PROJECT_STRUCTURE.md               # This file
├── Makefile                           # Common commands
├── setup.py                           # Python package setup
├── pyproject.toml                     # Dependencies & config
│
├── backend/                           # FastAPI backend
│   ├── Dockerfile
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py              # Health check endpoint
│   │       └── search.py              # Search endpoints (Phase 1)
│   │
│   ├── config.py                      # Settings & configuration
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py                      # Session management
│   │   └── models.py                  # SQLAlchemy models
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── base.py                    # Base repository class
│   │   └── document.py                # Document repository
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── search.py                  # Search service (Phase 1)
│   │   ├── opensearch.py              # OpenSearch (Phase 2)
│   │   ├── graph.py                   # Graph service (Phase 3)
│   │   ├── agent.py                   # Agent service (Phase 4)
│   │   └── llm.py                     # LLM service (Phase 4)
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   └── neo4j_client.py            # Neo4j operations (Phase 3)
│   │
│   └── search/
│       ├── __init__.py
│       └── opensearch.py              # OpenSearch ops (Phase 2)
│
├── frontend/
│   ├── gradio/
│   │   ├── Dockerfile
│   │   └── app.py                     # Gradio UI (推奨)
│   └── streamlit/
│       ├── Dockerfile
│       └── app.py                     # Streamlit UI
│
├── cli/                               # CLI (Phase 6)
│   ├── __init__.py
│   └── fde_cli.py                     # CLI commands
│
├── cdk/                               # AWS CDK (Phase 5)
│   ├── package.json
│   ├── tsconfig.json
│   ├── lib/
│   │   └── fde_stack.py               # CDK stack definition
│   └── bin/
│       └── app.ts                     # CDK app entry
│
├── profiles/                          # Project profiles
│   ├── rag-basic.yaml                 # Basic RAG profile
│   ├── graph-rag.yaml                 # Graph RAG profile
│   └── agent-enabled.yaml             # Agent-enabled profile
│
├── scripts/
│   ├── init_db.py                     # Database initialization
│   ├── seed_documents.py              # Sample data seeding
│   └── seed_graph.py                  # Graph data seeding
│
├── tests/
│   ├── conftest.py                    # Test configuration
│   ├── unit/
│   │   ├── test_api_health.py         # Health check tests
│   │   └── test_api_search.py         # Search tests
│   │
│   └── integration/
│       ├── test_database.py           # Database integration tests
│       └── test_search.py             # Search integration tests
│
├── infra/
│   └── docker-compose.yml             # Docker Compose config
│
├── docs/
│   └── README.md                      # Documentation index
│
├── adr/                               # Architecture Decision Records
│   ├── 001-interface-first-architecture.md
│   ├── 002-local-aws-parity.md
│   └── README.md
│
├── .env.example                       # Environment template
├── .gitignore                         # Git ignore rules
├── .dockerignore                      # Docker ignore rules
├── .pre-commit-config.yaml            # Pre-commit hooks
├── .bandit.yaml                       # Bandit security config
│
├── .github/
│   └── workflows/
│       ├── test.yml                   # CI: Test & Lint
│       └── deploy.yml                 # CD: Deploy to AWS
│
└── LICENSE                            # License
```

## File Descriptions

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation & overview |
| `QUICKSTART.md` | Get started in 5 minutes |
| `ARCHITECTURE.md` | System design & component breakdown |
| `IMPLEMENTATION_PLAN.md` | Phase 1-6 roadmap with details |
| `RUNBOOK.md` | Operations procedures & troubleshooting |
| `AGENTS.md` | Agent/LLM integration reference |
| `PROJECT_STRUCTURE.md` | This file - project layout |

### Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python dependencies & build config |
| `setup.py` | Package installation config |
| `.env.example` | Environment variables template |
| `.pre-commit-config.yaml` | Git hooks for code quality |
| `.bandit.yaml` | Security scanning config |

### Backend (`backend/`)

| Module | Phase | Purpose |
|--------|-------|---------|
| `api/main.py` | 1 | FastAPI application setup |
| `api/routes/` | 1-4 | HTTP endpoints by feature |
| `config.py` | 1 | Settings & environment config |
| `database/models.py` | 1 | SQLAlchemy ORM models |
| `database/db.py` | 1 | Database session management |
| `repositories/` | 1-3 | Data access layer |
| `services/` | 1-4 | Business logic layer |
| `search/opensearch.py` | 2 | Search implementation |
| `graph/neo4j_client.py` | 3 | Graph database client |

### Frontend (`frontend/`)

| File | Phase | Purpose |
|------|-------|---------|
| `gradio/app.py` | 1 | Gradio web UI |
| `gradio/Dockerfile` | 1 | Frontend container |

### Infrastructure

| File | Phase | Purpose |
|------|-------|---------|
| `infra/docker-compose.yml` | 1-4 | Local container orchestration |
| `cdk/lib/fde_stack.py` | 5 | AWS infrastructure as code |
| `cdk/package.json` | 5 | Node.js dependencies for CDK |

### CLI & Profiles (Phase 6)

| File | Purpose |
|------|---------|
| `cli/fde_cli.py` | CLI commands (init, up, down, deploy) |
| `profiles/rag-basic.yaml` | Basic RAG configuration |
| `profiles/graph-rag.yaml` | Graph-enabled configuration |
| `profiles/agent-enabled.yaml` | Full AI agent stack |

### Testing

| File | Type | Phase | Purpose |
|------|------|-------|---------|
| `tests/conftest.py` | Setup | 1 | Test configuration & fixtures |
| `tests/unit/test_api_health.py` | Unit | 1 | Health check tests |
| `tests/unit/test_api_search.py` | Unit | 1 | Search endpoint tests |
| `tests/integration/test_database.py` | Integration | 1 | Database layer tests |

### Scripts

| File | Phase | Purpose |
|------|-------|---------|
| `scripts/init_db.py` | 1 | Create/reset database schema |
| `scripts/seed_documents.py` | 1 | Load sample documents |
| `scripts/seed_graph.py` | 3 | Load sample graph data |

### CI/CD

| File | Purpose |
|------|---------|
| `.github/workflows/test.yml` | Test & lint on every PR |
| `.github/workflows/deploy.yml` | Deploy to AWS on main branch |

## Phase Dependencies

### Phase 1: Core
```
backend/config.py
backend/api/main.py
backend/database/models.py
backend/repositories/base.py, document.py
backend/services/search.py
frontend/gradio/app.py
tests/unit/test_api_*.py
```

### Phase 2: Search
```
Phase 1 + 
backend/services/opensearch.py
backend/search/opensearch.py
```

### Phase 3: Graph
```
Phase 2 +
backend/services/graph.py
backend/graph/neo4j_client.py
scripts/seed_graph.py
```

### Phase 4: Agent/LLM
```
Phase 3 +
backend/services/agent.py
backend/services/llm.py
```

### Phase 5: AWS CDK
```
cdk/lib/fde_stack.py
cdk/package.json
.github/workflows/deploy.yml
```

### Phase 6: CLI & Profiles
```
cli/fde_cli.py
profiles/*.yaml
scripts/seed_*.py
```

## Important Files to Know

### For Development
- `pyproject.toml` - Add dependencies here
- `backend/config.py` - Update settings
- `Makefile` - Common commands

### For Operations
- `.env.example` - Environment setup
- `RUNBOOK.md` - Operational procedures
- `infra/docker-compose.yml` - Container services

### For Deployment
- `cdk/lib/fde_stack.py` - AWS infrastructure
- `.github/workflows/deploy.yml` - CI/CD pipeline

### For Learning
- `ARCHITECTURE.md` - System design
- `adr/` - Architecture decisions
- `docs/` - Additional documentation

## Adding New Features

1. **Add a model**: `backend/database/models.py`
2. **Add a repository**: `backend/repositories/new_repo.py`
3. **Add a service**: `backend/services/new_service.py`
4. **Add routes**: `backend/api/routes/new_route.py`
5. **Add tests**: `tests/unit/test_new_*.py`
6. **Update config**: `backend/config.py`
7. **Add to docker-compose**: `infra/docker-compose.yml`

## Naming Conventions

- **Classes**: PascalCase (DocumentRepository, SearchService)
- **Functions**: snake_case (get_document, search_index)
- **Files**: snake_case (document.py, search.py)
- **Models**: Singular (Document, not Documents)
- **Databases**: plural (documents table)

## Code Organization Principles

1. **Single Responsibility**: One class = one job
2. **Dependency Injection**: FastAPI Depends()
3. **Repository Pattern**: Encapsulate data access
4. **Service Layer**: Business logic separation
5. **No Circular Imports**: Use TYPE_CHECKING if needed
6. **Type Hints**: All public functions
7. **Async/Await**: Throughout the stack
