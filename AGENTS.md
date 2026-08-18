# Agent / LLM 統合設計

## 概要

FDE PoC 基盤における Agent Runtime と LLM Provider の統合設計。

**重要な設計原則:**
- Interface 第一：openCypher / SPARQL / S3 API などのインターフェースを基準
- Agent からの直接 SDK アクセス禁止：Tool/Service Interface 経由のみ
- Factory/DI パターン：実装を動的に選択
- ローカル OSS ↔ AWS Managed：同一 Interface で差し替え可能

---

## Agent Runtime

### Local Runtime
- **Framework**: Strands Agents / LangGraph
- **実装**: `backend/agent/runtime/local.py`
- **対応**: 同期 / ストリーム実行

### AWS AgentCore Runtime
- **実装**: `backend/agent/runtime/agentcore.py`
- **特徴**: Multi-turn メモリ対応

**Interface**: `backend/agent/runtime/base.py`

---

## LLM Provider

### Local Provider (Ollama)
- **エンドポイント**: `http://ollama:11434`
- **モデル**: qwen3:8b (デフォルト)
- **埋め込み**: bge-m3
- **実装**: `backend/llm/provider/local.py`

### AWS Bedrock Provider
- **実装**: `backend/llm/provider/bedrock.py`
- **特徴**: 複数モデル対応

**Interface**: `backend/llm/provider/base.py`

---

## Tool Framework

Agent が利用する統一 Tool Interface。

**実装**: `backend/agent/tools/base.py`

### 組み込み Tool
- **SearchTool**: OpenSearch 検索
- **GraphTool**: Neo4j / Neptune クエリ

---

## Factory / DI

**実装**: `backend/agent/factory.py`

```python
# Agent Runtime 生成
runtime = AgentRuntimeFactory.create(config)

# LLM Provider 生成
llm = LLMProviderFactory.create(config)

# Service 統合
service = AgentServiceFactory.create(project_config)
```

---

## project.yaml 設定

### Fully Local

```yaml
agent:
  enabled: true
  runtime: local
  framework: strands
  config:
    max_turns: 10

llm:
  enabled: true
  provider: local
  config:
    engine: ollama
    endpoint: http://ollama:11434
    model: qwen3:8b
    embedding_model: bge-m3
```

### Hybrid (Local Agent + Bedrock)

```yaml
agent:
  enabled: true
  runtime: local
  framework: langgraph

llm:
  enabled: true
  provider: bedrock
  config:
    region: ap-northeast-1
    model_id: anthropic.claude-3-sonnet-20240229-v1:0
```

### AWS Production

```yaml
agent:
  enabled: true
  runtime: agentcore
  config:
    agent_id: arn:aws:agentcore:...

llm:
  enabled: true
  provider: bedrock
  config:
    model_id: anthropic.claude-3-opus-20240229-v1:0
```

---

## Backend API

**Endpoint**: `backend/api/agent.py`

- `POST /agent/execute` - Agent 実行
- `GET /agent/status` - 状態確認
- `WebSocket /agent/stream` - ストリーム実行

---

## テスト

**Location**: `tests/unit/agent/` 及び `tests/integration/agent/`

- Runtime テスト
- Provider テスト
- Service 統合テスト
- Tool テスト

---

## 実装フェーズ

| Phase | 対応項目 | 期間 |
|-------|---------|------|
| Phase 1 | 最小PoC（Agent なし） | Week 1-2 |
| **Phase 4** | **Agent/LLM 統合** | **Week 6-7** |
| Phase 5 | AWS CDK | Week 8-9 |

---

## 参考資料

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 実装ロードマップ
- [fde_modular_ai_platform_handoff_v2.md](docs/requirements/fde_modular_ai_platform_handoff_v2.md) - 全体設計
- [ADR/002 - Local ↔ AWS Parity](adr/002-local-aws-parity.md)
- [RUNBOOK.md](RUNBOOK.md) - 起動・デプロイ手順
