# FDE Template — 新規プロジェクト立ち上げガイド

このテンプレートから新しいAI/RAGプロジェクトを始める手順。

---

## Step 1: テンプレートのベースコピー

### GitHub Web UI で作成

1. GitHub で [fde-template](https://github.com/Noriaki-4/fde-template) を開く
2. **Use this template** ボタンをクリック
3. リポジトリ名・説明を入力 (e.g., `my-legal-rag`, `my-knowledge-graph`)
4. **Create repository from template** をクリック

### または CLI で実施

```bash
# 新規リポジトリを作成してテンプレートをコピー
gh repo create my-rag-project --template Noriaki-4/fde-template --private

# クローン
git clone https://github.com/YOUR_ORG/my-rag-project.git
cd my-rag-project
```

---

## Step 2: プロジェクト初期化

### プロジェクト情報の更新

```bash
# README.md の プロジェクト名を変更
# LICENSE を適切なものに変更
# .git/config でリモート URL を確認

git remote -v
```

### プロファイル選択

```bash
# どの構成で始めるか選択
# profiles/*.yaml を確認

cat profiles/rag-basic.yaml      # 基本的なRAG
cat profiles/graph-rag.yaml      # グラフ付きRAG
cat profiles/agent-enabled.yaml  # Agent + LLM
cat profiles/aws-production.yaml # AWS本番構成
```

### project.yaml を作成

```bash
cp profiles/rag-basic.yaml project.yaml

# 必要に応じてカスタマイズ
# cat project.yaml
```

---

## Step 3: 環境設定

### 環境変数設定

```bash
# テンプレートをコピー
cp .env.example .env

# エディタで編集
nano .env
```

**重要な設定項目:**

```bash
# LLM選択
LLM_PROVIDER=ollama              # local Gemma 4
LLM_MODEL=gemma:4-e4b           # またはqwen:7b, mistral:7b

# または AWS
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# AWS 環境の場合
AWS_REGION=ap-northeast-1
```

---

## Step 4: 環境構築

### 依存関係インストール

```bash
# Python 仮想環境
python3.11 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate   # Windows

# uv でインストール（推奨）
uv install -e ".[dev]"

# または pip
pip install -e ".[dev]"
```

### Docker イメージの準備

```bash
# 必要なコンテナをプル
docker compose pull

# または全て起動
docker compose up -d
```

---

## Step 5: 初回起動テスト

### Phase 1: コア RAG

```bash
# コンテナ起動
make up

# データベース初期化
make db-init

# サンプルデータ投入
make seed

# バックエンド起動 (ターミナル 1)
make backend
# → http://localhost:8000/docs

# フロントエンド起動 (ターミナル 2)
make frontend
# → http://localhost:7860
```

### 動作確認

1. **API ヘルスチェック**
   ```bash
   curl http://localhost:8000/health
   # {"status": "healthy"}
   ```

2. **フロントエンド表示**
   - http://localhost:7860 にアクセス
   - 「System Status」タブで backend 接続確認

3. **検索テスト** (Phase 2+)
   ```bash
   curl -X POST http://localhost:8000/search/ \
     -H "Content-Type: application/json" \
     -d '{"query": "test"}'
   ```

---

## Step 6: プロジェクト固有のカスタマイズ

### ディレクトリ構成例

```
my-rag-project/
├── backend/
│   ├── api/routes/
│   │   └── domain.py          # ← ドメイン固有エンドポイント
│   ├── services/
│   │   └── domain_service.py  # ← ビジネスロジック
│   └── repositories/
│       └── domain_repo.py     # ← データアクセス
├── frontend/
│   └── gradio/
│       └── app.py             # ← UI カスタマイズ
├── projects/
│   └── your-project/          # ← プロジェクト固有ファイル
│       └── project.yaml
└── docs/
    └── architecture.md        # ← プロジェクト設計書
```

### ファイル追加手順

1. **新しい API エンドポイント**
   ```python
   # backend/api/routes/domain.py
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.post("/analyze")
   async def analyze_document(content: str):
       # ドメイン固有ロジック
       return {"result": "..."}
   ```

2. **main.py に登録**
   ```python
   from backend.api.routes import domain
   app.include_router(domain.router, prefix="/domain", tags=["domain"])
   ```

3. **テスト追加**
   ```bash
   tests/unit/test_domain_*.py
   ```

---

## Step 7: データソース準備

### ドキュメント投入

```bash
# S3/MinIO にアップロード
aws s3 cp documents/ s3://my-bucket/documents/ --recursive

# または scripts/seed_*.py でサンプル投入
uv run python scripts/seed_documents.py
```

### グラフデータ投入（Phase 3+）

```bash
# Neo4j または Virtuoso に初期化
uv run python scripts/seed_graph.py
```

---

## Step 8: CI/CD 設定

### GitHub Actions

```bash
# ワークフロー確認
cat .github/workflows/test.yml
cat .github/workflows/deploy.yml

# テスト実行
make test

# カバレッジ確認
make coverage
```

### デプロイ準備（Phase 5+）

```bash
# AWS 認証情報設定
aws configure

# CDK デプロイ
cd cdk
npm install
npm run deploy
```

---

## Step 9: 本番準備

### チェックリスト

- [ ] プロジェクト固有ファイル追加完了
- [ ] API エンドポイント実装完了
- [ ] テストカバレッジ 80% 達成
- [ ] CI/CD パイプライン動作確認
- [ ] ドキュメント更新完了
- [ ] Docker イメージテスト完了
- [ ] AWS デプロイ設定完了

### デプロイ

```bash
# ローカルで最終確認
make verify

# ステージング環境
make deploy  # または cdk deploy --profile staging

# 本番環境
make deploy  # または cdk deploy --profile prod
```

---

## トラブルシューティング

### ポート競合

```bash
# ポート確認
lsof -i :8000
lsof -i :7860

# 別ポートで起動
cd backend && uvicorn api.main:app --reload --port 8001
```

### Docker エラー

```bash
# コンテナリセット
docker compose down -v
docker compose up -d

# ログ確認
docker logs fde-postgresql
docker logs fde-backend
```

### LLM エラー（Ollama）

```bash
# Ollama 起動確認
curl http://localhost:11434/api/tags

# モデルプル
ollama pull gemma:4-e4b
```

---

## 次のステップ

1. **API ドキュメント作成** → docs/api.md
2. **デモデータ準備** → projects/your-project/
3. **UI カスタマイズ** → frontend/gradio/app.py
4. **本番デプロイ** → cdk/ 設定
5. **監視・ログ** → RUNBOOK.md 参照

---

## よくある質問

**Q: ローカルと AWS で設定を変えたい**
- A: project.yaml で `llm.provider: ollama` vs `bedrock` を切り替え、.env で設定

**Q: 複数のプロジェクトを同じテンプレートから**
- A: 推奨。各プロジェクトが独立したレポとして管理される

**Q: テンプレート改善したい**
- A: このテンプレートレポに PR 送信。あるいは fork して管理

---

## サポート

- **ドキュメント**: [README.md](README.md), [ARCHITECTURE.md](ARCHITECTURE.md)
- **トラブル**: [RUNBOOK.md](RUNBOOK.md)
- **計画**: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **API**: http://localhost:8000/docs
