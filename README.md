# FDE Template — Modular AI/RAG Platform

Modular, production-ready foundation for AI PoC (Phases 1-9) supporting local OSS ↔ AWS parity.

## Quick Navigation

**📖 Documentation** → [`docs/`](docs/)

- **Start here**: [USAGE.md](docs/USAGE.md) — How to use this template for your project
- **Quick start**: [QUICKSTART.md](docs/QUICKSTART.md) — 5-minute local setup
- **Architecture**: [ARCHITECTURE.md](docs/ARCHITECTURE.md) — System design & components
- **Setup guide**: [SETUP.md](docs/SETUP.md) — Detailed installation
- **Implementation**: [IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) — Phase roadmap
- **Operations**: [RUNBOOK.md](docs/RUNBOOK.md) — Troubleshooting & deployment
- **Structure**: [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) — Directory layout

---

## What is FDE Template?

A modular, battle-tested foundation for building AI systems with:

- **Phase 1-3**: Core RAG (Search + Graph databases)
- **Phase 4**: Agent/LLM integration (Ollama + Bedrock)
- **Phase 5**: AWS CDK infrastructure
- **Phase 6**: CLI tooling & profiles
- **Phase 7-9**: Production features (NoSQL, AgentCore, GenU Chat)

**Local ↔ AWS**: Switch configs via `project.yaml` — develop locally, deploy to AWS.

---

## Repository Structure

```
fde-template/
├── README.md              # This file (index)
├── docs/                  # All documentation
│   ├── USAGE.md          # Start here for new projects
│   ├── QUICKSTART.md
│   ├── ARCHITECTURE.md
│   └── ...
├── backend/              # Python/FastAPI
├── frontend/             # Gradio UI
├── infra/                # Docker Compose
├── cdk/                  # AWS IaC (Phase 5)
├── tests/                # Test suite
├── scripts/              # Utilities
├── profiles/             # Config templates
├── adr/                  # Architecture decisions
└── projects/             # Project-specific files
```

---

## Quick Start

```bash
# 1. Use as template (GitHub UI: "Use this template")
gh repo create my-project --template Noriaki-4/fde-template

cd my-project

# 2. Choose config
cp profiles/rag-basic.yaml project.yaml

# 3. Setup environment
cp .env.example .env
uv install -e ".[dev]"

# 4. Run locally
make up
make backend      # Terminal 1
make frontend     # Terminal 2
```

→ [Full setup guide](docs/QUICKSTART.md)

---

## Features by Phase

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Core RAG (FastAPI + PostgreSQL + OpenSearch) | ✅ |
| 2 | Semantic Search (Vector embeddings) | ✅ |
| 3 | Graph Databases (Neo4j + Virtuoso) | ✅ |
| 4 | Agent/LLM (Ollama + Bedrock) | ✅ |
| 5 | AWS CDK Infrastructure | ✅ |
| 6 | CLI & Profiles | ✅ |
| 7 | NoSQL (ScyllaDB + DynamoDB) | ✅ |
| 8 | AgentCore + Canonical Graph | ✅ |
| 9 | GenU Chat + RAG Service | ✅ |

---

## Local vs. AWS

Select via `project.yaml`:

```yaml
# Local (Ollama)
llm:
  provider: ollama
  model: gemma:4-e4b

# AWS (Bedrock)
llm:
  provider: bedrock
  bedrock_model_id: anthropic.claude-3-5-sonnet-20241022-v2:0
```

Same code, different infrastructure.

---

## Support

- **Troubleshooting**: [RUNBOOK.md](docs/RUNBOOK.md)
- **Architecture**: [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **API Docs**: http://localhost:8000/docs (after running)
- **Config Schema**: [docs/project-schema.md](docs/project-schema.md)

---

## License

MIT — Fork, adapt, contribute.

---

**→ Start with [USAGE.md](docs/USAGE.md)**
