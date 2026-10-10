# Agent / LLM 統合設計

## 概要

FDE PoC 基盤における LLM Provider の統合設計と、Agent Runtime の実装状況。

**重要な設計原則:**
- Interface 第一：openCypher / SPARQL / S3 API などのインターフェースを基準
- Factory/DI パターン：`ServiceFactory`（`backend/factory.py`）で実装を動的に選択
- ローカル OSS ↔ AWS Managed：同一 Interface で差し替え可能

---

## LLM Provider（実装・配線済み）

**Interface**: `LLMService`（`backend/services/llm.py`）

### Ollama Provider（ローカル）
- **実装**: `OllamaLLMService`（`backend/services/llm.py`）
- **エンドポイント**: `config.ollama_base_url`（デフォルト `http://host.docker.internal:11434`）
- **モデル**: `config.llm_model`（デフォルト `gemma:4-e4b`。`qwen:7b`, `mistral:7b` 等も指定可）

### Bedrock Provider（AWS）
- **実装**: `BedrockLLMService`（`backend/services/bedrock.py`）
- **モデル ID**: `config.bedrock_model_id`（デフォルト `anthropic.claude-3-5-sonnet-20241022-v2:0`）

### 生成方法

```python
# backend/factory.py
llm_service = ServiceFactory.create_llm_service(config)
# config.llm_provider が "ollama" または "bedrock" で分岐
```

### API での利用

`backend/api/routes/genu_chat.py` の `POST /chat/conversations/{id}/messages` が
`llm_service.complete(message)` を実際に呼び出す（起動時に `main.py` が
`llm_service` を初期化し、ルート側は `Depends` で取得）。

---

## project.yaml / 環境変数での設定

`backend/config.py` の `Settings`（`pydantic-settings`、`.env.local` から読み込み）:

```bash
# ローカル (Ollama)
LLM_PROVIDER=ollama
LLM_MODEL=gemma:4-e4b
OLLAMA_BASE_URL=http://host.docker.internal:11434

# AWS (Bedrock)
LLM_PROVIDER=bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_REGION=ap-northeast-1
```

`llm_provider` に有効な値は `"ollama"` と `"bedrock"` のみ（`"local"` は不可）。

---

## Property Graph / RDF（独立して併用可能）

`GRAPH_ENABLED`（Neo4j / openCypher）と `RDF_ENABLED`（Virtuoso / SPARQL）は
互いに独立したフラグで、**両方同時に有効化できる**（ハイブリッドグラフ構成）。

```bash
GRAPH_ENABLED=true
GRAPH_ENGINE=neo4j

RDF_ENABLED=true
RDF_ENGINE=virtuoso
```

`RAGService`（`backend/services/rag.py`）は `graph_service` と `rdf_service` を
両方受け取り、`include_graph=true` のとき両方に対してクエリを実行する設計になっている
（`/rag/search` エンドポイント）。以前は単一の `rdf_model` フラグ
（`"property_graph" | "rdf"` の排他選択）で両者を同時に有効化できず、
RAGService の設計と矛盾していたため、`graph_enabled` / `rdf_enabled` の
独立フラグに分離した。

---

## Agent（実装のみ・未配線）

**Interface**: `AgentService`（`backend/services/agent.py`）— このコードベースの
他の全サービス（`GraphService`, `RDFService`, `LLMService`, `NoSQLRepository`,
`OpenSearchInterface`）と同じ、プリミティブ引数（`query: str`, `context: dict`）
の ABC + 実装パターンに統一されている。

| クラス | ファイル | 状態 |
|---|---|---|
| `AgentService` (ABC), `LocalAgentService` | `backend/services/agent.py` | 未配線 |
| `AgentCoreService` | `backend/agent/agentcore.py` | 未配線。`AgentService` を実装。boto3 `bedrock-agentcore` サービスと `invoke_agent_runtime` API を使用（要 `boto3>=1.34.0`） |

以下のクラスはコードとして存在し `AgentService` を正しく実装しているが、
`ServiceFactory` に対応する `create_*` メソッドがなく、`backend/api/main.py`
からも一切参照されない。API エンドポイントも存在しない（`/agent/*` ルートは無い）。
有効化するには Factory メソッドの追加・`main.py` への起動時配線・ルートファイルの
新規作成が必要（`nosql`/`opensearch` が追加されたときと同じ手順、`PROJECT_STRUCTURE.md`
の「Adding New Features」参照）。

> 以前は `AgentRuntime`（dataclass ベースの別 ABC、`backend/agent/runtime.py`）が
> 並存し、`AgentCoreRuntime` がそれを継承しながら実際には `AgentService` 型の
> シグネチャで実装されている不整合（LSP 違反）があった。`AgentRuntime` を廃止し、
> `AgentCoreService` として `AgentService` を直接実装する形に統合済み。

---

## Jobs（実装・配線済み）

汎用のジョブ実行基盤。具体的なジョブ（スクレイピング等）は含まず、サンプル `hello` /
`hello-pipeline` のみ。詳細は [docs/JOBS.md](docs/JOBS.md)、設計は
[adr/004-job-execution.md](adr/004-job-execution.md)。

- ジョブ追加: `backend/jobs/definitions/` に `@register_job("name")` を付けた `Job` サブクラスを置く
  （`JOB_MODULES` のパッケージは起動時に自動 import）
- 実行: `LocalJobLauncher`（subprocess）/ `EcsJobLauncher`（ECS RunTask）を
  `ServiceFactory.create_job_launcher(config, SessionLocal)` が `JOB_LAUNCHER=local|ecs` で選択。
  `main.py` が起動時に生成し `/jobs/*` から利用
- ジョブ本体のコマンドはローカル・ECS 共通: `python -m backend.jobs exec <job> --run-id <id>`
- **状態はジョブに書かせない**: プロセス終了 / ECS Task State Change から `RunEvent` を作り
  `RunEventHandler` だけが `job_runs.status` を更新する（OOM kill でも failed になる）
- パイプライン: `backend/jobs/pipelines/*.yaml`。ローカルは `LocalPipelineRunner`、AWS は Step Functions（CDK 未実装）
- 実行記録: Postgres の `job_runs` / `run_artifacts`。成果物は MinIO/S3 の `runs/{root_run_id}/{job}/`

## RAG 文書台帳（モデル・リポジトリのみ）

[adr/003-rag-data-layers.md](adr/003-rag-data-layers.md)。原本 = S3、メタデータとリネージの正本 =
Postgres の `catalog_documents` / `catalog_document_targets`（`CatalogRepository`）、
OpenSearch / Neo4j / RDF は再構築可能な派生ストア。API はまだ無く、取り込みジョブから直接使う。
既存の `documents` テーブル + `SearchService` は OpenSearch 無効時の簡易検索として残している（台帳とは別物）。

---

## テスト

**Location**: `tests/unit/`（フラット構成、`agent/` サブディレクトリなし）

配線済み機能のテスト:
- `test_api_health.py`, `test_api_search.py` — Health / Search
- `test_api_rag.py` — RAG（`/rag/*`）
- `test_api_nosql.py` — NoSQL（`/nosql/*`）
- `test_api_opensearch.py` — OpenSearch（`/opensearch/*`）
- `test_genu_chat.py` — Chat（`/chat/*`、LLM 呼び出しはフェイクでモック）
- `test_canonical_graph.py` — Canonical Graph データモデル
- `test_job_*.py`, `test_api_jobs.py` — Jobs（レジストリ、イベント、ローカル実行は実 subprocess + sqlite ファイル DB、
  パイプライン、ECS 起動・イベント変換はフェイク boto3 クライアント、CLI）。テスト専用ジョブは `tests/fixtures/jobs/`
- `test_catalog.py` — RAG 文書台帳
- `test_object_store.py` — S3/MinIO オブジェクトストア

Agent Runtime 層（未配線）のテストは存在しない。

---

## 参考資料

- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) - 実装ロードマップ
- [docs/requirements/fde_modular_ai_platform_handoff_v2.md](docs/requirements/fde_modular_ai_platform_handoff_v2.md) - 全体設計
- [adr/002-local-aws-parity.md](adr/002-local-aws-parity.md)
- [adr/003-rag-data-layers.md](adr/003-rag-data-layers.md) - RAG データ 3 層化と文書台帳
- [adr/004-job-execution.md](adr/004-job-execution.md) - ジョブ実行基盤
- [docs/JOBS.md](docs/JOBS.md) - ジョブの追加・実行方法
- [docs/RUNBOOK.md](docs/RUNBOOK.md) - 起動・デプロイ手順
