# Complete Setup Guide

Step-by-step instructions for setting up the FDE Template development environment.

## Prerequisites

### System Requirements
- macOS 11+ / Ubuntu 20.04+ / Windows 10+ (with WSL2)
- 4GB RAM minimum (8GB recommended)
- 10GB free disk space

### Software Requirements
- Python 3.11 or later
- Docker & Docker Compose
- Node.js 22.x
- Git
- A text editor or IDE (VS Code, PyCharm, etc.)

## Step 1: System Preparation

### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required tools
brew install python@3.11 docker docker-compose node git

# Install Docker Desktop (recommended)
brew install --cask docker
```

### Ubuntu
```bash
# Update package manager
sudo apt update && sudo apt upgrade

# Install dependencies
sudo apt install -y python3.11 python3-pip docker.io docker-compose nodejs git

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Windows (WSL2)
```bash
# In PowerShell as Administrator
wsl --install
wsl --install -d Ubuntu-22.04

# Inside WSL terminal
sudo apt update && sudo apt upgrade
sudo apt install -y python3.11 python3-pip docker.io nodejs git
```

## Step 2: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/fde-template.git
cd fde-template

# Or initialize a new repository
git init
git remote add origin https://github.com/your-org/fde-template.git
```

## Step 3: Python Environment Setup

### Option A: Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
uv install -e ".[dev]"
```

### Option B: Using venv

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"
```

## Step 4: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment (optional - defaults work for local development)
# Linux/macOS:
nano .env

# macOS (with default editor):
open -e .env

# Windows (Notepad):
notepad .env
```

### Key Environment Variables

```bash
# Database (Phase 1)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fde

# MinIO Storage (Phase 1)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin
MINIO_ENDPOINT=http://localhost:9000

# OpenSearch (Phase 2)
OPENSEARCH_URL=http://localhost:9200

# Neo4j (Phase 3)
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j

# Ollama (Phase 4)
OLLAMA_BASE_URL=http://localhost:11434

# AWS (Phase 5)
AWS_REGION=ap-northeast-1
```

## Step 5: Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Set up git hooks
pre-commit install

# Run pre-commit on all files (first time)
pre-commit run --all-files
```

## Step 6: Node.js Setup (For CDK)

```bash
# Verify Node.js version
node --version  # Should be 22.x

# Install CDK dependencies
cd cdk
npm install
cd ..
```

## Step 7: Start Docker Services

### Option A: All Services (Phase 4+)
```bash
docker compose -f infra/docker-compose.yml up -d
```

### Option B: Selective Services (Phase 1 only)
```bash
docker compose -f infra/docker-compose.yml --profile with-core up -d
```

### Option C: With Search (Phase 2)
```bash
docker compose -f infra/docker-compose.yml --profile with-search up -d
```

### Option D: With Graph (Phase 3)
```bash
docker compose -f infra/docker-compose.yml --profile with-graph up -d
```

### Verify Services
```bash
# Check service status
docker compose -f infra/docker-compose.yml ps

# View logs
docker compose -f infra/docker-compose.yml logs -f

# Test PostgreSQL
psql postgresql://postgres:postgres@localhost:5432/fde -c "SELECT version();"

# Test MinIO
curl http://localhost:9000

# Test OpenSearch (Phase 2+)
curl http://localhost:9200

# Test Neo4j (Phase 3+)
curl http://localhost:7474
```

## Step 8: Initialize Database

```bash
# Initialize schema
uv run python scripts/init_db.py

# Seed sample data
uv run python scripts/seed_documents.py

# Seed graph data (Phase 3+)
uv run python scripts/seed_graph.py
```

## Step 9: Verify Installation

```bash
# Run tests
uv run pytest -v

# Check linting
uv run ruff check .

# Type check
uv run mypy backend/

# Security scan
uv run bandit -r backend/
```

## Step 10: Start Development Server

### Terminal 1: Backend API
```bash
cd backend
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Frontend UI
```bash
cd frontend/gradio
uv run python app.py
```

### Terminal 3: Watch Tests
```bash
uv run pytest -v --watch
```

Access the application:
- Frontend: http://localhost:7860
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Troubleshooting

### Python Version Issue
```bash
# Verify Python version
python --version

# If wrong version, specify explicitly
python3.11 -m pip install uv
python3.11 -m uv install -e ".[dev]"
```

### Docker Issues
```bash
# Check Docker daemon
docker ps

# Rebuild containers
docker compose -f infra/docker-compose.yml down
docker compose -f infra/docker-compose.yml up -d --build

# Check disk space
docker system df
```

### Database Connection Error
```bash
# Check PostgreSQL
docker logs fde-postgres

# Reset database
uv run python scripts/init_db.py --reset

# Check connection string
echo $DATABASE_URL
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use different port
cd backend && uvicorn api.main:app --reload --port 8001
```

### Memory Issues
```bash
# Increase Docker memory (Mac)
# Settings → Resources → Memory: 8GB

# Increase Docker memory (Linux)
docker run --memory=8g ...

# Check current memory
docker stats
```

## Next Steps

1. **Read Documentation**
   - Start with `README.md`
   - Review `ARCHITECTURE.md` for system design
   - Check `IMPLEMENTATION_PLAN.md` for phases

2. **Explore Codebase**
   - `backend/api/routes/` - HTTP endpoints
   - `backend/services/` - Business logic
   - `backend/repositories/` - Data access

3. **Make Your First Contribution**
   - Create a feature branch
   - Make changes
   - Run tests and linting
   - Create a pull request

4. **Deploy Locally**
   - Follow `RUNBOOK.md` for operational procedures
   - Set up AWS credentials for CDK
   - Test `fde` CLI commands

## Development Workflow

### Daily Workflow
```bash
# 1. Start services
make up

# 2. Start backend
make backend

# 3. Start frontend (new terminal)
make frontend

# 4. Make changes to code

# 5. Tests run automatically
# 6. Pre-commit hooks check code quality

# 7. Stop services
make down
```

### Before Committing
```bash
# 1. Run all tests
make test

# 2. Check coverage
make coverage

# 3. Lint code
make lint

# 4. Format code
make format

# 5. Verify
make verify
```

### Deploying
```bash
# 1. Ensure main branch
git checkout main

# 2. Review changes
git log --oneline -5

# 3. Deploy to AWS
make deploy
```

## Environment Setup Checklist

- [ ] Python 3.11+ installed
- [ ] Docker & Docker Compose installed
- [ ] Node.js 22.x installed
- [ ] Git configured
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] .env file configured
- [ ] Pre-commit hooks installed
- [ ] Docker services running
- [ ] Database initialized
- [ ] Tests passing
- [ ] Backend server running
- [ ] Frontend server running

## Getting Help

**Documentation:**
- Architecture: `ARCHITECTURE.md`
- Implementation: `IMPLEMENTATION_PLAN.md`
- Operations: `RUNBOOK.md`
- Project Structure: `PROJECT_STRUCTURE.md`

**Troubleshooting:**
- Check error logs
- Run `make verify` to diagnose issues
- Review `RUNBOOK.md` troubleshooting section
- Check GitHub issues and discussions

**Support:**
- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- GitHub Wiki: Community knowledge
