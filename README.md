# FDE Template — Modular AI PoC Platform

**Forward Deployed Engineer 向けの再利用可能な AI PoC 基盤**

## 概要

複数プロジェクトの短期間での生成AI / RAG / GraphRAG / AI Agent PoC を立ち上げるためのスターター基盤。

**重視するポイント:**
- ✓ ローカル（OSS）で低コスト開発
- ✓ AWS Managed Service への置き換え可能
- ✓ プロジェクトごとに機能 ON/OFF
- ✓ ローカル ↔ AWS で同じコード

---

## クイックスタート

### 前提条件

```bash
python --version   # 3.11.x
docker --version   # 最新
```

### 起動（Phase 1 最小構成）

```bash
# 1. リポジトリクローン
git clone https://github.com/your-org/fde-template.git
cd fde-template

# 2. 環境ファイル作成
cp .env.example .env.local

# 3. コンテナ起動
docker compose -f infra/docker-compose.yml up -d

# 4. ヘルスチェック
curl http://localhost:8000/health

# 5. UI アクセス
open http://localhost:7860  # Gradio
open http://localhost:8000/docs  # API Docs
```

---

## アーキテクチャ

```
┌──────────────────────────────────────────┐
│           Gradio UI (7860)               │
├──────────────────────────────────────────┤
│         FastAPI Backend (8000)           │
├─────────────────┬──────────────────┬──────┤
│   PostgreSQL    │     MinIO        │Search│
│    (5432)       │    (9000)        │ (*)  │
└─────────────────┴──────────────────┴──────┘
  (*) Phase 2+: OpenSearch (9200)
  (*) Phase 3+: Neo4j (7687) + Virtuoso SPARQL (8890)
```

---

## ドキュメント

| ファイル | 説明 |
|---------|------|
| [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | 実装ロードマップ (Phase 1-6) |
| [AGENTS.md](AGENTS.md) | Agent / LLM 設計 (Phase 4+) |
| [RUNBOOK.md](RUNBOOK.md) | 起動・デプロイ手順 |
| [adr/](adr/) | アーキテクチャ決定記録 |

---

## ディレクトリ構成

```
fde-template/
├── backend/
│   ├── api/
│   │   ├── main.py          # FastAPI アプリケーション
│   │   ├── routes/          # API ルーター
│   │   └── __init__.py
│   ├── config.py            # 設定管理
│   ├── Dockerfile
│   └── __init__.py
│
├── frontend/
│   └── gradio/
│       ├── app.py           # Gradio UI
│       └── Dockerfile
│
├── infra/
│   └── docker-compose.yml   # サービス構成
│
├── pyproject.toml           # Python 依存関係
├── IMPLEMENTATION_PLAN.md   # ロードマップ
├── RUNBOOK.md              # 手順書
├── AGENTS.md               # Agent 設計
└── README.md               # このファイル
```

---

## 開発ガイド

### ローカル開発（Virtual Env）

```bash
# Python 環境構築
python3.11 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -e ".[dev]"

# テスト実行
pytest tests/ -v
```

### Backend API 開発

```bash
cd backend
uvicorn api.main:app --reload
# http://localhost:8000/docs で Swagger UI を確認
```

### Docker での開発

```bash
# ビルド
docker compose -f infra/docker-compose.yml build

# 起動
docker compose -f infra/docker-compose.yml up -d

# ログ確認
docker compose -f infra/docker-compose.yml logs -f backend
```

---

## Phase ロードマップ

| Phase | 期間 | 主要機能 |
|-------|------|---------|
| **Phase 1** | Week 1-2 | ✓ FastAPI + PostgreSQL + MinIO + Gradio |
| Phase 2 | Week 3 | OpenSearch 統合 |
| Phase 3 | Week 4-5 | Neo4j / RDF Graph 対応 |
| Phase 4 | Week 6-7 | Agent / LLM 統合 |
| Phase 5 | Week 8-9 | AWS CDK デプロイ |
| Phase 6 | Week 10 | CLI / Profile 化 |

**現在:** Phase 1（実装中）

---

## 主な特徴

### Interface First Architecture
- DB 製品ではなく、openCypher / SPARQL / S3 API などのインターフェースを基準
- Neo4j ↔ Neptune、MinIO ↔ S3 の置き換えが容易

### Local ↔ AWS Parity
- ローカルと AWS で同じアプリケーションコード
- Config（project.yaml）で動作環境を切り替え

### Modular Design
- 各機能を ON/OFF できる（project.yaml）
- プロジェクトに必要な機能だけ有効化

---

## 本番デプロイ（Phase 5+）

```bash
cd cdk
cdk deploy --require-approval=never
```

詳細は [RUNBOOK.md](RUNBOOK.md) を参照。

---

## サポート

- **設計**: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **起動手順**: [RUNBOOK.md](RUNBOOK.md)
- **トラブルシューティング**: [RUNBOOK.md#8-トラブルシューティング](RUNBOOK.md#8-トラブルシューティング)

---

## ライセンス

Internal Use Only
