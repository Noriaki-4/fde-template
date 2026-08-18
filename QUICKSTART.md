# FDE Template Quick Start Guide

Get up and running with FDE in 5 minutes.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Node.js 22.x (for AWS CDK)
- Git

## 1. Clone & Install

```bash
git clone https://github.com/your-org/fde-template.git
cd fde-template

# Install dependencies
uv venv
source .venv/bin/activate
uv install -e ".[dev]"

# Install CDK dependencies (Phase 5)
cd cdk && npm install && cd ..
```

## 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings (optional, defaults work for local)
```

## 3. Start Containers

```bash
# Phase 1 (Core only)
fde up

# Phase 2 (with OpenSearch)
docker compose -f infra/docker-compose.yml --profile with-search up -d

# Phase 3 (with Neo4j)
docker compose -f infra/docker-compose.yml --profile with-graph up -d

# All services
docker compose -f infra/docker-compose.yml up -d
```

## 4. Initialize Database

```bash
uv run python scripts/init_db.py
uv run python scripts/seed_documents.py
uv run python scripts/seed_graph.py  # Phase 3+
```

## 5. Launch Backend

```bash
# Terminal 1: Backend API
cd backend
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## 6. Launch Frontend

```bash
# Terminal 2: Gradio UI
cd frontend/gradio
uv run python app.py
```

Access UI at: **http://localhost:7860**

API docs at: **http://localhost:8000/docs**

## 7. Test Search (Phase 1)

```bash
# Index a document
curl -X POST http://localhost:8000/search/index \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Document",
    "content": "FastAPI is amazing",
    "metadata": {"category": "tutorial"}
  }'

# Search
curl -X POST http://localhost:8000/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "FastAPI"}'
```

## 8. Deploy to AWS (Phase 5)

```bash
cd cdk

# Review changes
npm run diff

# Deploy infrastructure
npm run deploy

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name FdeStack \
  --query 'Stacks[0].Outputs'
```

## Verification Checklist

- [ ] Backend running at http://localhost:8000
- [ ] Frontend running at http://localhost:7860
- [ ] Health check passes: `curl http://localhost:8000/health`
- [ ] Search index works
- [ ] Database has seeded data
- [ ] Tests pass: `uv run pytest -v`

## Troubleshooting

**Port already in use:**
```bash
lsof -i :8000
kill -9 <PID>
```

**Database connection failed:**
```bash
# Check PostgreSQL
docker logs fde-postgres

# Reset database
uv run python scripts/init_db.py --reset
```

**Neo4j not starting:**
```bash
# Check logs
docker logs fde-neo4j

# Increase JVM memory
export NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
docker compose up -d
```

**OpenSearch heap error:**
```bash
# Set memory limits in docker-compose.yml
environment:
  - discovery.type=single-node
  - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
```

## Next Steps

1. Read [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for detailed phase information
2. Review [Architecture Decision Records](adr/) for design rationale
3. Check [RUNBOOK.md](RUNBOOK.md) for operational procedures
4. Explore [docs/](docs/) for additional documentation

## CLI Commands (Phase 6)

```bash
# Initialize new project
fde init my-project --profile rag-basic

# Start containers
fde up

# Stop containers
fde down

# Validate config
fde validate

# Deploy to AWS
fde deploy --region ap-northeast-1
```

## Profiles

- **rag-basic**: Search-only (PostgreSQL + MinIO + OpenSearch)
- **graph-rag**: Graph-enabled (+ Neo4j with openCypher)
- **agent-enabled**: Full stack (+ Ollama + LLM Agent)

## Performance Tips

- Use `--profile` to run only needed services
- Enable Redis caching for high-traffic scenarios
- Set up OpenSearch replicas for production
- Configure connection pooling in SQLAlchemy

## Support

- Issues: https://github.com/your-org/fde-template/issues
- Discussions: https://github.com/your-org/fde-template/discussions
- Docs: https://docs.fde-template.dev
