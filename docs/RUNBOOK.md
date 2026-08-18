# RUNBOOK — 起動・デプロイ手順

## 1. ローカル開発環境セットアップ

### 1.1 前提条件

```bash
# バージョン確認
python --version           # 3.11.x
node --version            # 22.x (CDK 用)
docker --version          # 最新
docker compose --version  # 2.x+

# Python 環境
uv --version              # uv パッケージマネージャー
```

### 1.2 初期セットアップ

```bash
# リポジトリクローン
git clone https://github.com/your-org/fde-template.git
cd fde-template

# Python 仮想環境
uv venv
source .venv/bin/activate

# 依存関係インストール
uv pip install -r requirements.txt
uv pip install -r requirements-dev.txt

# Node 依存関係 (CDK 用)
cd cdk
npm install
cd ..
```

### 1.3 設定ファイル作成

```bash
# .env.local をプロジェクト設定から生成
cp .env.example .env.local

# 以下を編集 (.env.local)
cat .env.local | grep -E "DATABASE_URL|MINIO_|LLM_"
```

**必須環境変数:**

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fde_poc

# Storage
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=knowledge-root

# LLM (ローカル)
LLM_PROVIDER=local
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=qwen3:8b
EMBEDDING_MODEL=bge-m3

# LLM (Bedrock - オプション)
# LLM_PROVIDER=bedrock
# AWS_REGION=ap-northeast-1
```

---

## 2. Docker Compose で起動

### 2.1 Phase 1 最小構成の起動

```bash
# コンテナ起動 (PostgreSQL + MinIO + FastAPI + Gradio)
docker compose up -d

# ログ確認
docker compose logs -f

# ヘルスチェック
curl http://localhost:8000/health
curl http://localhost:9000/minio/health/live
curl http://localhost:5432 &>/dev/null && echo "PostgreSQL OK"
```

**アクセス URL:**
- Backend API: http://localhost:8000
- Gradio UI: http://localhost:7860
- MinIO Console: http://localhost:9001
- PostgreSQL: localhost:5432

### 2.2 OpenSearch 追加（Phase 2）

```bash
# docker-compose.yml で opensearch セクションを uncomment

docker compose up -d opensearch opensearch-dashboards

# ヘルスチェック
curl -u admin:Passw0rd! http://localhost:9200

# Dashboards: http://localhost:5601
```

### 2.3 Neo4j 追加（Phase 3）

```bash
# docker-compose.yml で neo4j セクションを uncomment

docker compose up -d neo4j

# ヘルスチェック
curl http://localhost:7474

# Browser: http://localhost:7474
# Credentials: neo4j / password
```

### 2.4 コンテナ停止

```bash
# すべて停止
docker compose down

# データ永続化を保持（ボリューム保持）
docker compose down --remove-orphans

# ボリューム削除（リセット）
docker compose down -v
```

---

## 3. Backend API 操作

### 3.1 API エンドポイント

**ドキュメント:**
```bash
# Swagger UI
open http://localhost:8000/docs

# ReDoc
open http://localhost:8000/redoc
```

### 3.2 検索 API

```bash
# ドキュメントインデックス
curl -X POST http://localhost:8000/search/index \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "id": "doc-1",
        "title": "サンプル文書",
        "content": "これはサンプルドキュメントです"
      }
    ]
  }'

# 検索実行
curl -X GET "http://localhost:8000/search?q=サンプル&limit=10"
```

### 3.3 Agent API

```bash
# Agent 実行
curl -X POST http://localhost:8000/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "PostgreSQL のバージョンは？",
    "stream": false
  }'

# Agent ステータス
curl http://localhost:8000/agent/status
```

### 3.4 Graph Query (Phase 3+)

```bash
# グラフクエリ実行
curl -X POST http://localhost:8000/graph/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "MATCH (n) RETURN n LIMIT 10",
    "params": {}
  }'
```

---

## 4. ローカル Ollama セットアップ

### 4.1 Ollama インストール

```bash
# macOS
brew install ollama

# Linux
curl https://ollama.ai/install.sh | sh

# または Docker
docker run -d \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama
```

### 4.2 モデルダウンロード

```bash
# Qwen 3 (8B)
ollama pull qwen3:8b

# BGE Embedding
ollama pull bge-m3

# Gemma (軽量)
ollama pull gemma:2b

# モデル一覧
ollama list
```

### 4.3 テスト

```bash
# API エンドポイント確認
curl http://localhost:11434/api/tags

# 生成テスト
curl -X POST http://localhost:11434/api/generate \
  -d '{
    "model": "qwen3:8b",
    "prompt": "Hello, how are you?",
    "stream": false
  }'
```

---

## 5. テスト実行

### 5.1 ユニットテスト

```bash
# すべてのテスト実行
uv run pytest tests/unit/ -v

# カバレッジ レポート
uv run pytest tests/unit/ --cov=backend --cov-report=html

# ブラウザで確認
open htmlcov/index.html
```

### 5.2 Integration テスト

```bash
# Docker Compose で環境起動
docker compose up -d

# Integration テスト実行
uv run pytest tests/integration/ -v

# 環境停止
docker compose down
```

### 5.3 E2E テスト（Phase 5+）

```bash
# 環境起動
docker compose up -d

# UI テスト実行
uv run pytest tests/e2e/ -v

# スクリーンショット確認
ls -la tests/e2e/screenshots/
```

---

## 6. デバッグ・ログ

### 6.1 ログ確認

```bash
# Backend ログ
docker compose logs -f backend

# Database ログ
docker compose logs -f postgresql

# 全ログ
docker compose logs -f
```

### 6.2 コンテナ内シェル

```bash
# Backend
docker compose exec backend bash

# PostgreSQL
docker compose exec postgresql psql -U postgres -d fde_poc

# MinIO
docker compose exec minio sh
```

### 6.3 Database クエリ

```bash
# PostgreSQL 接続
psql -h localhost -U postgres -d fde_poc

# テーブル一覧
\dt

# スキーマ確認
\d table_name

# クエリ実行
SELECT * FROM documents LIMIT 10;
```

---

## 7. AWS デプロイ（Phase 5）

### 7.1 前提条件

```bash
# AWS CLI 設定
aws configure

# 認証確認
aws sts get-caller-identity

# Node.js CDK
node --version  # 22.x
npm install -g aws-cdk
cdk --version
```

### 7.2 CDK デプロイ

```bash
cd cdk

# スタック一覧確認
cdk list

# デプロイ前確認
cdk diff FDETemplate

# デプロイ実行
cdk deploy FDETemplate --require-approval=never

# CloudFormation スタック確認
aws cloudformation describe-stacks --stack-name FDETemplate
```

### 7.3 環境変数設定（AWS）

```bash
# ECS Task Definition に環境変数を設定
aws ecs register-task-definition \
  --family fde-template-backend \
  --container-definitions '[
    {
      "name": "backend",
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "LLM_PROVIDER", "value": "bedrock"},
        {"name": "AWS_REGION", "value": "ap-northeast-1"}
      ]
    }
  ]'
```

### 7.4 デプロイ確認

```bash
# ECS サービス確認
aws ecs describe-services --cluster fde-template --services backend

# CloudFront ディストリビューション確認
aws cloudfront list-distributions

# API エンドポイント確認
aws apigateway get-rest-apis
```

---

## 8. トラブルシューティング

### 8.1 ポート競合

```bash
# ポート確認
lsof -i :8000
lsof -i :5432
lsof -i :9000

# プロセス終了
kill -9 <PID>

# 別ポートで起動
docker compose -e "BACKEND_PORT=8001" up
```

### 8.2 Database 接続エラー

```bash
# PostgreSQL 再起動
docker compose restart postgresql

# ボリューム削除（リセット）
docker compose down -v
docker compose up -d

# ログ確認
docker compose logs postgresql
```

### 8.3 LLM 接続エラー

```bash
# Ollama 確認
curl http://localhost:11434/api/tags

# Ollama 再起動
docker restart ollama

# モデル確認
ollama list

# ダウンロード再試行
ollama pull qwen3:8b
```

### 8.4 Docker イメージ更新

```bash
# キャッシュクリア
docker compose build --no-cache

# 古いイメージ削除
docker image prune -a

# 再起動
docker compose up -d
```

---

## 9. 本番環境チェックリスト

### デプロイ前

- [ ] すべてのテストが PASS
- [ ] ユニットテスト: 80%+ カバレッジ
- [ ] Integration テスト実行済み
- [ ] セキュリティスキャン完了
- [ ] ログレベル本番設定に変更
- [ ] 機密情報は環境変数に移動

### デプロイ後

- [ ] ヘルスチェック確認
- [ ] エラーログ監視
- [ ] パフォーマンスモニタリング起動
- [ ] バックアップ設定確認
- [ ] ロードバランサー設定確認
- [ ] CDN キャッシュ設定確認

---

## 10. よく使うコマンド

```bash
# 全起動
docker compose up -d && sleep 5 && curl http://localhost:8000/health

# 全停止
docker compose down

# ログ確認（リアルタイム）
docker compose logs -f --tail=100

# テスト実行
uv run pytest tests/ -v --cov

# DB マイグレーション
uv run python backend/scripts/migrate.py

# キャッシュクリア
docker compose exec redis redis-cli FLUSHALL

# データベースリセット
docker compose down -v && docker compose up -d postgresql && sleep 10

# 本番デプロイ
cd cdk && cdk deploy --require-approval=never && cd ..
```

---

## 参考資料

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 実装ロードマップ
- [AGENTS.md](AGENTS.md) - Agent/LLM 設計
- [docker-compose.yml](../../infra/docker-compose.yml) - サービス構成
- AWS デプロイ: `cdk/README.md`
- API ドキュメント: `http://localhost:8000/docs`
