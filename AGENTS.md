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

## Agent Runtime（実装のみ・未配線）

以下のクラスはコードとして存在するが、`ServiceFactory` に対応する
`create_*` メソッドがなく、`backend/api/main.py` からも一切参照されない。
API エンドポイントも存在しない（`/agent/*` ルートは無い）。有効化するには
Factory メソッドの追加・`main.py` への起動時配線・ルートファイルの新規作成が必要。

| クラス | ファイル | 状態 |
|---|---|---|
| `AgentRuntime` (ABC), `LocalAgentRuntime` | `backend/agent/runtime.py` | 未配線 |
| `AgentCoreRuntime` | `backend/agent/agentcore.py` | 未配線。boto3 `bedrock-agentcore` サービスと `invoke_agent_runtime` API を使用（要 `boto3>=1.34.0`） |
| `AgentService` (ABC), `LocalAgentService` | `backend/services/agent.py` | 未配線 |

**既知の不整合**: `AgentCoreRuntime.invoke(query: str, context: dict)` は
親クラス `AgentRuntime.invoke(request: AgentRequest) -> AgentResponse`
のシグネチャと一致していない（`AgentService` 側のシグネチャに揃っている）。
現状どちらのクラスからも呼ばれていないため実害はないが、配線時は
シグネチャの整合を取ること。

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

Agent Runtime 層（未配線）のテストは存在しない。

---

## 参考資料

- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) - 実装ロードマップ
- [docs/requirements/fde_modular_ai_platform_handoff_v2.md](docs/requirements/fde_modular_ai_platform_handoff_v2.md) - 全体設計
- [adr/002-local-aws-parity.md](adr/002-local-aws-parity.md)
- [docs/RUNBOOK.md](docs/RUNBOOK.md) - 起動・デプロイ手順
