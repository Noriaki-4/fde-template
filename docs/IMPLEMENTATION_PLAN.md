# FDE Template 実装計画

## 概要

FDE 向けモジュール型 AI PoC 基盤を段階的に実装。`local-rag-poc-law` での実装経験を活かしつつ、複数プロジェクトに再利用可能な基盤を構築。

**目標**: `fde init customer-poc --profile graph-rag` で即座に PoC を起動可能にする。

---

## 実装戦略

### バージョン管理ポリシー

**Python 環境:**
- Python 3.11.x (LTS, 2027年10月まで サポート)
- uv パッケージマネージャー
- pyproject.toml で依存関係を一元管理

**Docker イメージバージョン:**
- PostgreSQL 16 (latest stable)
- Neo4j 5.26.1 Community
- OpenSearch 2.19.1
- MinIO RELEASE.2025-04-22 (偶数月リリース版)
- Ollama latest (ローカル開発用)

**Node.js (CDK 用):**
- Node.js 22.x LTS
- AWS CDK 2.x (latest)

**主要ライブラリ:**
- FastAPI 0.115.x
- Pydantic 2.10.x
- Neo4j Python 5.27.x
- Boto3 1.28.x (AWS)
- OpenSearch-py 2.x

### 複雑性管理

**依存関係の層別化:**
```
Layer 1 (基本)
├─ FastAPI, Pydantic, Uvicorn
├─ PostgreSQL driver
├─ MinIO client

Layer 2 (検索/Graph)
├─ Neo4j driver
├─ OpenSearch client
├─ Requests

Layer 3 (LLM/Agent)
├─ Ollama HTTP client
├─ Anthropic SDK
├─ AWS SDK

Layer 4 (ツール)
├─ Reranker (HuggingFace)
├─ Embedding model
└─ Evaluation framework
```

---

## Phase 別実装ロードマップ

### Phase 1: 最小ローカル PoC (Week 1-2)

**成果物:**
- Gradio UI
- FastAPI Backend
- PostgreSQL
- MinIO
- Docker Compose (これら 4 つ)

**ディレクトリ構成:**
```
fde-template/
├─ backend/
│  ├─ api/
│  │  ├─ main.py (FastAPI app)
│  │  ├─ routes/
│  │  │  ├─ health.py
│  │  │  ├─ documents.py
│  │  │  └─ search.py
│  │  ├─ services/
│  │  │  ├─ search_service.py
│  │  │  └─ storage_service.py
│  │  ├─ repositories/
│  │  │  └─ base.py
│  │  └─ config.py
│  └─ Dockerfile
│
├─ frontend/
│  ├─ gradio/
│  │  ├─ app.py
│  │  └─ requirements.txt
│  └─ Dockerfile
│
├─ infra/
│  ├─ docker-compose.yml
│  └─ docker/
│     └─ (custom Dockerfiles for specialized services)
│
├─ profiles/
│  └─ rag-basic.yaml
│
├─ projects/
│  └─ example/
│     └─ project.yaml
│
└─ pyproject.toml
```

**バージョン定義:**

```toml
# backend/pyproject.toml
[project]
name = "fde-backend"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "fastapi==0.115.6",
    "uvicorn[standard]==0.34.0",
    "pydantic==2.10.4",
    "pydantic-settings==2.3.4",
    "psycopg[binary]==3.20.1",
    "minio==7.2.13",
    "requests==2.32.3",
]

[tool.uv]
allow-direct-references = true
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  postgresql:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: fde_poc
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 30

  minio:
    image: minio/minio:RELEASE.2025-04-22T22-12-26Z
    command: server /data --console-address ':9001'
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD-SHELL", "curl -fs http://localhost:9000/minio/health/live >/dev/null || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 30

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgresql:5432/fde_poc
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: minioadmin
      MINIO_SECRET_KEY: minioadmin
    ports:
      - "8000:8000"
    depends_on:
      postgresql:
        condition: service_healthy
      minio:
        condition: service_healthy

  gradio:
    build: ./frontend/gradio
    ports:
      - "7860:7860"
    environment:
      BACKEND_URL: http://backend:8000
    depends_on:
      - backend

volumes:
  postgres_data:
  minio_data:
```

**依存バージョン検証:**
```bash
# Python 依存関係
python -m pip show fastapi uvicorn pydantic minio psycopg

# Docker イメージバージョン
docker image ls --filter reference=postgres:16-alpine
docker image ls --filter reference=minio/minio:RELEASE.2025-04-22T22-12-26Z
```

---

### Phase 2: OpenSearch 統合 (Week 3)

**追加:**
- OpenSearch 2.19.1
- OpenSearch Dashboards 2.19.1
- Search Service
- Document indexing

**新規依存:**
- opensearch-py==2.6.0

**バージョン確認:**
```bash
curl http://localhost:9200
curl http://localhost:5601
```

---

### Phase 3: Graph DB 対応 (Week 4-5)

**追加:**
- Neo4j 5.26.1 Community (Property Graph)
- Apache Jena + RDF4J オプション (RDF)
- GraphService
- Adapter パターン (Neo4j / Neptune)

**新規依存:**
```toml
neo4j==5.27.0
rdflib==7.1.1  # RDF支援
```

**環境変数での切り替え（`GRAPH_ENABLED` と `RDF_ENABLED` は独立、両方 true でハイブリッド構成可）:**
```bash
GRAPH_ENABLED=true
GRAPH_ENGINE=neo4j

RDF_ENABLED=true
RDF_ENGINE=virtuoso
```

---

### Phase 4: Agent / LLM 統合 (Week 6-7)

**実装・配線済み:**
- `LLMService` Interface + `OllamaLLMService`（`backend/services/llm.py`）
- `BedrockLLMService`（`backend/services/bedrock.py`）
- `ServiceFactory.create_llm_service` で `llm_provider` 設定から生成
- `backend/api/routes/genu_chat.py` の Chat API から実際に呼び出し

**実装済みだが未配線:**
- `AgentService` Interface + `LocalAgentService`（`backend/services/agent.py`）
- `AgentCoreService`（`backend/agent/agentcore.py`、`AgentService` を実装）
- Tool Framework は未実装（`SearchTool`/`GraphTool` 等のクラスは存在しない）

詳細は [AGENTS.md](../AGENTS.md) を参照。

**依存関係:**
```toml
anthropic==0.42.0        # Bedrock 経由の Claude 呼び出し
ollama==0.4.4            # ローカル LLM クライアント
langgraph>=0.1.0         # Agent 層の依存（宣言のみ、未使用）
langchain-core>=0.1.0    # 同上
```

**Ollama 設定例:**
```bash
# .env.local
LLM_PROVIDER=ollama
LLM_MODEL=gemma:4-e4b
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

---

### Phase 5: AWS CDK 実装 (Week 8-9)

**追加:**
- CDK TypeScript
- VPC / Storage / Database / Search / Graph / App Stack
- RDS PostgreSQL → from PostgreSQL
- S3 → from MinIO
- Neptune → from Neo4j
- OpenSearch Service → from OpenSearch OSS
- Bedrock → from Ollama
- AgentCore Runtime → from Local Agent

**新規ファイル:**
```
cdk/
├─ package.json (Node.js 22.x)
├─ tsconfig.json
├─ lib/
│  ├─ vpc-stack.ts
│  ├─ storage-stack.ts
│  ├─ database-stack.ts
│  ├─ search-stack.ts
│  ├─ graph-stack.ts
│  ├─ app-stack.ts
│  └─ fde-template-stack.ts
├─ bin/
│  └─ fde-template.ts
└─ cdk.json
```

**package.json:**
```json
{
  "name": "fde-cdk",
  "version": "0.1.0",
  "description": "AWS CDK for FDE template",
  "scripts": {
    "cdk": "cdk",
    "deploy": "cdk deploy --all",
    "destroy": "cdk destroy --all"
  },
  "dependencies": {
    "aws-cdk-lib": "^2.165.0",
    "constructs": "^10.4.2"
  },
  "devDependencies": {
    "typescript": "~5.6.2"
  }
}
```

---

### Phase 6: CLI / Profile 化 (Week 10)

**CLI ツール:**
```
fde-cli/
├─ cli.py
├─ commands/
│  ├─ init.py
│  ├─ up.py
│  ├─ down.py
│  ├─ validate.py
│  ├─ deploy.py
│  └─ destroy.py
└─ config/
   ├─ profiles.yaml
   └─ schemas/
      
```

**Profile定義:**
```yaml
# profiles/rag-basic.yaml
profile: rag-basic
ui:
  enabled: true
  type: gradio
database:
  relational:
    enabled: true
    engine: postgresql
storage:
  enabled: true
  engine: minio
search:
  enabled: true
  engine: opensearch
graph:
  enabled: false
agent:
  enabled: false
```

---

## 版バージョン依存関係マトリックス

| Component | Local Dev | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 (AWS) |
|-----------|-----------|---------|---------|---------|---------|---------------|
| Python | 3.11.x | ✓ | ✓ | ✓ | ✓ | ✓ |
| FastAPI | 0.115.6 | ✓ | ✓ | ✓ | ✓ | ✓ |
| PostgreSQL | 16 | ✓ | ✓ | ✓ | ✓ | RDS 16 |
| MinIO | 2025-04-22 | ✓ | ✓ | ✓ | ✓ | S3 |
| OpenSearch | - | - | 2.19.1 | 2.19.1 | 2.19.1 | Service |
| Neo4j | - | - | - | 5.26.1 | 5.26.1 | Neptune |
| Ollama | latest | - | - | - | ✓ | Bedrock |
| Strands | - | - | - | - | ✓ | - |
| AWS CDK | - | - | - | - | - | 2.165.x |
| Node.js | - | - | - | - | - | 22.x |

---

## 依存関係解決戦略

### 1. Python 依存関係の管理

**uv の活用:**
```bash
# インストール
uv venv
uv pip install -r requirements.txt

# 新規追加
uv add fastapi

# ロックファイル生成
uv pip compile requirements.txt -o requirements.lock
```

**バージョン固定のメリット:**
- 再現可能性の確保
- CI/CD での動作保証
- チーム内の環境統一

### 2. Docker イメージ版バージョンの固定

**Digest ハッシュによる固定:**
```dockerfile
FROM postgres:16-alpine@sha256:xxxxx
FROM minio/minio:RELEASE.2025-04-22T22-12-26Z@sha256:xxxxx
```

**バージョンチェックスクリプト:**
```bash
#!/bin/bash
# scripts/validate-versions.sh
set -e

echo "=== Validating Docker versions ==="
docker image inspect postgres:16-alpine >/dev/null || exit 1
docker image inspect minio/minio:RELEASE.2025-04-22T22-12-26Z >/dev/null || exit 1

echo "=== Validating Python versions ==="
python --version | grep -q "3.11" || exit 1

echo "All versions OK"
```

### 3. 依存関係の競合回避

**セマンティック・バージョニングの采用:**
```toml
# pyproject.toml
dependencies = [
    "fastapi>=0.115,<0.116",      # Minor 版の固定
    "pydantic>=2.10,<2.11",
    "neo4j>=5.27,<5.28",
]
```

### 4. Phase 間での後方互換性

**Interface の安定化:**
- Service Layer の仕様を固定
- API Schema のバージョニング
- Migration スクリプトの用意

---

## 品質保証

### テスト戦略

**Unit Tests (80% 最小):**
```bash
uv run pytest tests/unit/ -v --cov=backend --cov-fail-under=80
```

**Integration Tests:**
```bash
uv run pytest tests/integration/ -v --docker-compose
```

**E2E Tests:**
```bash
# Phase 5 以降のみ
uv run pytest tests/e2e/ -v
```

### バージョン互換性テスト

```bash
# Docker Compose での動作確認
docker compose up -d
docker compose exec backend python -m pytest tests/
docker compose down
```

---

## リスク管理

### 高リスク項目

| 項目 | リスク | 対策 |
|------|--------|------|
| OpenSearch 互換性 | OSS vs Service の差異 | Integration test で検証 |
| Neo4j Cypher | Neptune openCypher 互換性 | openCypher のみ使用 |
| LLM Provider 切替 | Ollama ↔ Bedrock の互換性 | Adapter test で検証 |
| AWS CDK Stack 生成 | enabled フラグのマッピング漏れ | generated code review |

### バージョン更新方針

**セキュリティ脆弱性対応:**
- 重大 (CVSS 9.0+): 即座に更新
- 高 (CVSS 7.0-8.9): 次の週次リリースで対応
- 中以下: 定期更新 (月1回)

**新機能リリース:**
- マイナーバージョン: 次の Phase 開始時に検討
- メジャーバージョン: 新プロジェクト開始時のみ

---

## デリバリー予定

| Phase | 期間 | 主要成果物 | バージョン | 状態 |
|-------|------|-----------|----------|------|
| Phase 1 | Week 1-2 | Gradio + FastAPI + PostgreSQL | v0.1.0 | ✓ |
| Phase 2 | Week 3 | OpenSearch 統合 | v0.2.0 | ✓ |
| Phase 3 | Week 4-5 | Graph (Neo4j + Virtuoso RDF) | v0.3.0 | ✓ |
| Phase 4 | Week 6-7 | Agent + LLM (Ollama) | v0.4.0 | ✓ |
| Phase 5 | Week 8-9 | AWS CDK (RDS, S3, OpenSearch) | v0.5.0 | ✓ |
| Phase 6 | Week 10 | CLI + Profile (3種) | v1.0.0 | ✓ |
| Phase 7 | Week 11-12 | NoSQL + AWS Bedrock | v1.1.0 | ✓ |
| Phase 8 | Week 13-14 | AWS AgentCore + Graph中間形式 | v1.2.0 | △ 実装のみ、未配線 |
| Phase 9 | Week 15 | GenU 互換 Chat API | v1.3.0 | ✓ (Chat API のみ。GenU Adapter/Frontend は未実装) |

---

## Phase 7: NoSQL & AWS LLM (Week 11-12) — ✓ 完了・配線済み

**目標**: DynamoDB互換とAWS Bedrockの統合

`ServiceFactory.create_nosql_service` / `create_llm_service`（bedrock 分岐）から
生成され、`backend/api/main.py` の起動時に初期化、`backend/api/routes/nosql.py`
（`NOSQL_ENABLED=true` で `/nosql/*` を有効化）から実際に呼び出される。

**成果物:**

1. **NoSQL Layer**
   - `backend/database/nosql/`
   - BaseNoSQLRepository (abstract)
   - ScyllaDBAlternatorAdapter
   - DynamoDBAdapter
   - Config: `database.nosql.enabled`, `database.nosql.engine`

2. **LLM Provider Expansion**
   - `backend/services/bedrock.py`
   - BedrockLLMService (async)
   - Model routing (default/planner/generation/embedding/reranker)
   - Config: `llm.provider=bedrock`, `llm.region`, `llm.model_id`

3. **Docker Compose**
   - ScyllaDB Alternator (with-nosql profile)
   - Environment variables for Alternator

4. **Integration Tests**
   - NoSQL repository tests
   - Bedrock LLM tests (mock)
   - Adapter compatibility tests

5. **Documentation**
   - NoSQL schema examples
   - Bedrock Model ID mapping
   - Alternator互換性チェックリスト

**ファイル:**
```
backend/
├─ database/
│  └─ nosql/
│     ├─ base.py
│     ├─ scylladb.py
│     └─ dynamodb.py
├─ services/
│  └─ bedrock.py
tests/
├─ unit/
│  └─ test_nosql_*.py
└─ integration/
   └─ test_nosql_database.py
```

---

## Phase 8: AWS AgentCore & Graph Canonical Format (Week 13-14) — △ 実装のみ、未配線

**目標**: AWS本番向けAgent統合とGraph中間形式

**現状**: 以下のクラスはすべてコードとして存在し、単体では正しく動作するが、
`ServiceFactory` に対応する `create_*` メソッドがなく、`backend/api/main.py`
からも一切参照されない。有効化するには Factory メソッドの追加・起動時配線・
ルートファイルの新規作成が必要（詳細は [AGENTS.md](../AGENTS.md)）。

1. **AgentCore**
   - `backend/agent/agentcore.py`
   - `AgentCoreService`（`AgentService` を実装。`boto3` の `bedrock-agentcore` サービス、`invoke_agent_runtime` API を使用。`boto3>=1.34.0` 必須）
   - Config: 未実装（`agent.*` 系の設定項目は `backend/config.py` に存在しない）

2. **Graph Canonical Format**
   - `backend/graph/canonical/`
   - `CanonicalNode`, `CanonicalRelation`, `CanonicalGraph`（dataclass）
   - Graph transformer（Property/RDF → Canonical）
   - シリアライザ（`serializer.py`）

3. **Storage Layer**
   - `backend/storage/graph_store.py`
   - `GraphStorageService`（MinIO/S3 への永続化）
   - Factory メソッドなし、未配線

4. **Routes**
   - 計画時は `backend/api/routes/graph_canonical.py`（`GET /graph/export`, `POST /graph/import`）を想定していたが、**実装されていない**。該当ファイル・エンドポイントは存在しない。

5. **Tests**
   - `tests/unit/test_canonical_graph.py` — dataclass / transformer / serializer の単体テストのみ。Storage 層・API 層・AgentCore の呼び出しを通したテストは無い。

**ファイル:**
```
backend/
├─ agent/
│  └─ agentcore.py
├─ graph/
│  ├─ canonical/
│  │  ├─ models.py
│  │  ├─ transformer.py
│  │  └─ serializer.py
├─ storage/
│  └─ graph_store.py
├─ api/routes/
│  └─ graph_canonical.py
tests/
├─ unit/
│  ├─ test_canonical_format.py
│  └─ test_agentcore.py
└─ integration/
   └─ test_graph_storage.py
```

**Profile追加:**
- `profiles/aws-production.yaml`
- `profiles/hybrid-bedrock-local.yaml`

---

## Phase 9: GenU 互換 Chat API (Week 15) — ✓ Chat API のみ完了

**目標**: GenUのFrontendから独自Backendへの接続

**現状**: Chat/Conversation API と RAGService は実装・配線済み。GenU Adapter
レイヤーと GenU 側フロントエンドは計画時から実装されておらず、当面の予定もない。

1. **GenU Adapter** — 未実装
   - `backend/api/adapters/genu.py` は存在しない
   - GenU 側との Request/Response 変換レイヤーは無い

2. **Chat/Conversation API** — ✓ 実装・配線済み
   - `backend/api/routes/genu_chat.py`
   - `POST /chat/conversations`（会話作成）
   - `POST /chat/conversations/{conversation_id}/messages`（メッセージ送信、`llm_service.complete()` を実際に呼び出す）
   - `GET /chat/conversations/{conversation_id}`（会話取得。メッセージ一覧は会話オブジェクトに含まれる）
   - `GET /chat/conversations`（一覧）、`DELETE /chat/conversations/{conversation_id}`
   - 会話はインメモリ（`dict`）保存で、再起動すると消える。WebSocket ストリーミングは未実装。

3. **Unified Service Layer** — ✓ 実装・配線済み
   - `RAGService`（`backend/services/rag.py`）— Search + Graph + RDF 統合
   - `backend/api/routes/rag.py` — `POST /rag/search`, `GET /rag/context/{entity_id}`, `GET /rag/health`

4. **Frontend Config** — 未実装
   - `frontend/genu/` ディレクトリは存在しない（`frontend/gradio/`, `frontend/streamlit/` のみ）

**ファイル（実際に存在するもの）:**
```
backend/
├─ api/routes/
│  ├─ genu_chat.py
│  └─ rag.py
└─ services/
   └─ rag.py
```

---

## 技術選定 (Phase 7-9)

### NoSQL

| 観点 | ScyllaDB Alternator | DynamoDB |
|------|-------------------|----------|
| ローカル開発 | ✓ (コンテナ) | ✗ (LocalStack必要) |
| 互換性 | 70-80% (制限あり) | 100% |
| コスト | 最小化可能 | 従量課金 |
| 推奨用途 | 開発・ステージング | 本番 |

**DynamoDB制限への対応:**
- Alternator未実装: TTL、GSI の代替実装
- テストで互換性検証
- Alternator移行ガイドの提供

### LLM Provider (Bedrock)

**対応モデル:**
```
- テキスト生成: Claude 3 Sonnet/Opus
- 埋め込み: Titan Embeddings
- 画像認識: Claude 3 Vision
```

**ハイブリッド戦略:**
```yaml
llm:
  default: bedrock          # メイン
  planner: local/ollama     # 軽量タスク
  embedding: bedrock        # 高品質
```

### AgentCore

**対応:**
- AWS Agents for Bedrock
- Multi-turn memory
- Tool (Knowledge Base, API, Database)

**制限:**
- AgentCore自体のラッピング必要
- Local↔AWS の完全な切り替えは困難
- 本番案件では AWS推奨

### GenU

**戦略:**
- GenU Frontend のみ活用
- Backend API境界を明確に
- 完全な機能互換を目指さない
- カスタム Backend への接続優先

---

## 実装優先度 (Phase 7-9)

### 高優先度

1. **Phase 7: Bedrock LLM** (多くのAWS案件で必要)
2. **Phase 8: AgentCore Runtime** (本番環境の必須要件)

### 中優先度

3. **Phase 7: NoSQL (DynamoDB)** (GenU連携時に必要)
4. **Phase 8: Canonical Graph Format** (運用効率化)

### 低優先度

5. **Phase 9: GenU Frontend** (カスタムUI優先)

---

## リスク・制限

### Phase 7

- **Alternator互換性**: DynamoDB の全機能を実装していない
  - TTL、グローバルセカンダリインデックス (GSI) の一部
  - 互換性マトリックスを提供し、AWS移行時の差分を最小化

### Phase 8

- **AgentCore API**: AWS固有で、ローカル相当物がない
  - LangGraph/Strands を ローカル候補として維持
  - 切り替え戻し不可 (単方向マイグレーション)

### Phase 9

- **GenU カスタマイズ**: GenU本体への大きな改修は避ける
  - Frontend のコンポーネント利用に限定
  - 独立した Backend API 設計を優先

---

## 次のステップ

### Phase 1-6 (✓ 完了)

1. ✅ バージョン依存関係マトリックスの確認
2. ✅ AGENTS.md 作成 (Agent/LLM Interface 設計)
3. ✅ RUNBOOK.md 作成 (起動・デプロイ手順)
4. ✅ ADR (Architecture Decision Record) 作成
5. ✅ Phase 1-6 実装完了

### Phase 7-9 (→ 次フェーズ)

1. **Phase 7: NoSQL & Bedrock**
   - ScyllaDB Alternator setup
   - DynamoDBAdapter実装
   - BedrockLLMService実装
   - Integration tests

2. **Phase 8: AgentCore & Canonical Graph**
   - AgentCoreService実装
   - Canonical format transformer
   - Graph storage layer
   - S3/MinIO serialization

3. **Phase 9: GenU Frontend**
   - GenU adapter layer
   - Chat/Conversation API
   - RAG unified service
   - Frontend integration tests

---

## 技術スタック確認

### Phase 7-9 追加ライブラリ

```toml
[project.optional-dependencies]
# Phase 7
nosql = [
    "boto3>=1.34.0",  # DynamoDB
]
bedrock = [
    "anthropic>=0.42.0",  # Claude Bedrock
    "boto3>=1.34.0",  # bedrock-agentcore サービスに 1.34.0+ が必要
]

# Phase 8
graph-storage = [
    "pydantic>=2.10.4",  # Canonical models
    "jsonlines>=4.0.0",  # JSONL serialization
]

# Phase 9
genu = [
    "httpx>=0.27.0",  # GenU backend calls
    "websockets>=12.0",  # WebSocket support
]
```

### Docker Images

```yaml
# Phase 7
scylladb:
  image: scylladb/scylla:latest
  port: 9042

# Phase 8-9 (local development)
# No new images required
```

