# FDE向けモジュール型AI PoC基盤 — 設計引き継ぎドキュメント

## 1. 目的

FDE（Forward Deployed Engineer）が顧客案件ごとに短期間で生成AI / RAG / GraphRAG / AI Agent のPoCを立ち上げるための、再利用可能なスターター基盤を作る。

重視するポイントは以下。

- ローカルではOSS中心で低コストに動作確認できる
- AWSでは必要に応じてマネージドサービスへ置き換えられる
- プロジェクトごとに必要な機能だけON/OFFできる
- UI、DB、検索、Graph、Agentを疎結合にする
- ローカルとAWSでアプリケーションコードの変更を最小化する
- 高価なAWSマネージドサービスを常時起動せず、PoCでは必要時のみコンテナ起動できるようにする
- 将来的に `cdk deploy` で案件環境を短時間に構築できるようにする

## 2. 全体アーキテクチャ

```text
                  UI
        ┌─────────┴─────────┐
        │                   │
     Gradio              GenU UI
        │                   │
        └─────────┬─────────┘
                  │
             Backend API
                  │
      ┌───────────┼───────────────┐
      │           │               │
   Agent       Search           Graph
      │           │               │
      │       OpenSearch      ┌────┴─────┐
      │                       │          │
      │                 Property Graph   RDF
      │                    openCypher   SPARQL
      │
      ├─ RDB
      ├─ NoSQL
      └─ Object Storage
```

UIから個別DBへ直接接続しない。必ずBackend API / Service層を経由し、各実装をAdapterで切り替える。

## 3. ローカルOSSとAWSの対応

| Capability | Local / OSS | AWS Managed |
|---|---|---|
| UI | Gradio / GenU改修版 | GenU / ECS等 |
| Backend | FastAPI / Python | ECS Fargate / Lambda等 |
| RDB | PostgreSQL | RDS PostgreSQL |
| NoSQL | ScyllaDB + Alternator | DynamoDB |
| Object Storage | MinIO | S3 |
| Search | OpenSearch OSS | Amazon OpenSearch Service |
| Property Graph | Neo4j Community | Amazon Neptune |
| Property Graph Query | openCypher | openCypher |
| RDF | Apache Jena / RDF4J | Amazon Neptune |
| RDF Query | SPARQL | SPARQL |
| Agent | Local Python Agent | AgentCore Runtime |
| IaC | Docker Compose | AWS CDK |

## 4. UI方針

### 4.1 Gradio

最短でPoCを作るための標準UI。主用途はチャット、RAG検索デモ、GraphRAG、SQL生成、ファイルアップロード、表・結果表示、Agent実行。

### 4.2 GenU

AWS案件や本格的なユーザー検証ではGenUのUI/UXを活用する。ただし、GenU標準のAWSバックエンドへ強く依存させず、GenU Frontendから独自Backend APIへ接続できるようにする。

```text
GenU Frontend
      │
      ▼
GenU互換API / Adapter
      │
      ▼
共通Backend
```

GenU本体を全面改修するより、FrontendとBackendの境界を明確にする。

### 4.3 UIは差し替え可能にする

```yaml
ui:
  type: gradio
```

または、

```yaml
ui:
  type: genu
```

将来的にはReact / Next.js追加も可能とする。

## 5. Backend設計

BackendはFastAPI等で独立させる。

```text
backend/
├─ api/
├─ agent/
├─ search/
├─ graph/
├─ database/
├─ storage/
├─ repositories/
├─ services/
└─ config/
```

UIから個別実装へ直接アクセスさせない。

## 6. RDB

ローカルはPostgreSQL Container、AWSはRDS PostgreSQLを採用する。

保存対象例:

- ユーザー設定
- プロジェクト設定
- SQLメタデータ
- 実行履歴
- Agent設定
- データソース設定
- UI設定

BackendではRepository層を介する。

```text
RelationalRepository
├─ PostgreSQLAdapter
└─ RDSPostgreSQLAdapter
```

実際にはPostgreSQL互換なので、接続設定差分だけで済ませることを目標とする。

## 7. DynamoDB互換NoSQL

GenUではDynamoDBがチャット履歴、設定、ユースケース情報等の永続化に利用される。ローカルでDynamoDB互換環境を使いたい場合、ScyllaDB + Alternatorを候補とする。

```text
Local
ScyllaDB Alternator
        ↓
DynamoDB API

AWS
DynamoDB
```

Backend側ではAWS SDK等を使い、endpointのみ切り替える方式を優先する。ただしAlternatorはDynamoDB完全互換ではないため、GenUが実際に利用しているDynamoDB APIについて互換性検証が必要。

## 8. Object Storage

ローカルはMinIO、AWSはS3を採用する。PythonではS3互換APIを利用する。

ローカルのみendpointを設定する。

```text
S3_ENDPOINT=http://minio:9000
```

AWSではendpointを省略し、標準S3 endpointを利用する。

## 9. Search

ローカルはOpenSearch OSS Container、AWSはAmazon OpenSearch Serviceを採用する。PoCでは高価なマネージドOpenSearchを常時起動せず、必要時だけOSS OpenSearchコンテナを起動する構成を優先する。

検索Index自体をSource of Truthにしない。

```text
S3 / MinIO
   ↓
processed documents
   ↓
OpenSearch index
```

OpenSearchは再構築可能なDerived Dataとして扱う。

## 10. Graph DB

Graphはプロジェクトに応じて以下を選択可能にする。

```text
Graph
├─ Property Graph
│   └─ openCypher
│
└─ RDF
    └─ SPARQL
```

## 11. Property Graph

ローカルはNeo4j Community、AWSはAmazon Neptuneを採用する。クエリ言語はopenCypherに固定する。

重要なルール:

> Neo4jを標準にするのではなく、openCypherを標準インターフェースにする。

Neo4j固有機能、APOC等への依存は可能な限り避ける。

```text
Neo4j
   ↓ openCypher互換
Neptune
```

## 12. RDF

ローカルはApache JenaまたはRDF4J、AWSはAmazon Neptuneを採用する。クエリ言語はSPARQLとする。

RDFは法令、Knowledge Graph、オントロジー、概念体系、標準化された意味表現、外部Knowledge Graph連携などの案件で有利。

## 13. Graph Service

AgentやUIからCypher / SPARQLを直接呼ばせない。

```text
GraphService
   │
   ├─ PropertyGraphRepository
   │     ├─ Neo4jAdapter
   │     └─ NeptuneOpenCypherAdapter
   │
   └─ RDFRepository
         ├─ JenaAdapter
         └─ NeptuneSparqlAdapter
```

共通API例:

```python
get_node(id)
get_neighbors(id, relation=None)
find_path(source, target)
get_schema()
search_relations(...)
```

モデル固有機能も残す。

```text
PropertyGraph capability
- traverse
- shortest_path

RDF capability
- ontology query
- inference
- SHACL
```

完全共通化は狙わない。

## 14. Graphの中間形式

Graph DB自体をSource of Truthにしない。

```text
S3 / MinIO
└─ processed/
   └─ graph/
      ├─ canonical/
      ├─ property/
      └─ rdf/
```

Canonical Graph例:

```text
nodes.jsonl
relations.jsonl
concepts.jsonl
```

例:

```json
{
  "source": "ordinance-5",
  "relation": "BASED_ON",
  "target": "law-10"
}
```

これをProperty Graphでは `(ordinance-5)-[:BASED_ON]->(law-10)`、RDFでは `ordinance-5 legal:basedOn law-10` へ変換する。

## 15. Property Graphでの軽量オントロジー

Property Graphでも以下を使ってオントロジー風表現を可能にする。

```text
INSTANCE_OF
IS_A
SUBRELATION_OF
DOMAIN
RANGE
```

例:

```text
○○市条例
  ─INSTANCE_OF→ Ordinance

Ordinance
  ─IS_A→ LegalDocument

BASED_ON
  ─SUBRELATION_OF→ LegalRelation
```

GraphRAGではConcept Layer / Relation Definition Layer / Instance Layerの3層を推奨する。

## 16. Agent

Agentも切り替え可能にする。

ローカル:

```text
Python Agent
```

AWS:

```text
AgentCore Runtime
```

例:

```yaml
agent:
  enabled: true
  runtime: local
```

AWS:

```yaml
agent:
  enabled: true
  runtime: agentcore
```

AgentからDB実装へ直接アクセスせず、各ServiceをToolまたはAPIとして利用する。

## 17. ON/OFF機能

本基盤の最重要要件。プロジェクトごとに必要Capabilityのみ有効化する。

```yaml
project:
  name: legal-rag-poc

ui:
  enabled: true
  type: gradio

database:
  relational:
    enabled: true
    engine: postgresql

  nosql:
    enabled: false
    engine: alternator

storage:
  enabled: true
  engine: minio

search:
  enabled: true
  engine: opensearch

graph:
  enabled: true
  model: rdf
  engine: jena
  query_language: sparql

agent:
  enabled: true
  runtime: local

redis:
  enabled: false
```

## 18. AWS設定例

```yaml
project:
  name: legal-rag-prod

ui:
  enabled: true
  type: genu

database:
  relational:
    enabled: true
    engine: rds-postgresql

  nosql:
    enabled: true
    engine: dynamodb

storage:
  enabled: true
  engine: s3

search:
  enabled: false

graph:
  enabled: true
  model: rdf
  engine: neptune
  query_language: sparql

agent:
  enabled: true
  runtime: agentcore
```

## 19. ON/OFFとInfrastructureを連動させる

`enabled` はアプリの接続可否だけでなく、Infrastructure構築にも反映する。

```text
project.yaml
      │
      ├─ Docker Compose
      │    └─ enabled=trueのContainerのみ起動
      │
      └─ AWS CDK
           └─ enabled=trueのResourceのみ作成
```

例えば `search.enabled: false` なら、ローカルではOpenSearchを起動せず、AWSでもOpenSearch Resourceを作成しない。

## 20. Profile

個別フラグに加え、よく使う組み合わせをProfile化する。

### rag-basic

```text
Gradio
PostgreSQL
MinIO
OpenSearch
```

### graph-rag

```text
Gradio
PostgreSQL
MinIO
OpenSearch
Neo4j
```

### legal-knowledge-graph

```text
GenU
PostgreSQL
S3
OpenSearch
Jena / SPARQL
AgentCore
```

例:

```yaml
profile: graph-rag
```

Profile適用後に個別設定でoverrideできるようにする。

## 21. 必要時だけContainerを起動する

PoCコスト削減のため、以下は常時稼働させない構成を検討する。

- OpenSearch OSS
- Neo4j
- Jena
- ScyllaDB

例:

```text
fde up search
fde up graph
fde down search
fde down graph
```

または、`fde up` でproject.yamlのenabled項目のみまとめて起動する。

## 22. Source of Truth

検索DBやGraph DBを永続データの原本にしない。

```text
S3 / MinIO
├─ original/
└─ processed/
   ├─ documents/
   ├─ search/
   └─ graph/
```

OpenSearch / Neo4j / Jenaは原則として再構築可能なDerived Dataとして扱う。これによりContainer停止・再作成を容易にする。

## 23. 想定リポジトリ構成

```text
fde-starter/
├─ frontend/
│  ├─ gradio/
│  └─ genu/
│
├─ backend/
│  ├─ api/
│  ├─ agent/
│  ├─ search/
│  ├─ graph/
│  │  ├─ property/
│  │  └─ rdf/
│  ├─ database/
│  │  ├─ relational/
│  │  └─ nosql/
│  ├─ storage/
│  ├─ services/
│  ├─ repositories/
│  └─ config/
│
├─ graph/
│  ├─ canonical/
│  ├─ property/
│  │  ├─ schema/
│  │  └─ queries/
│  └─ rdf/
│     ├─ ontology/
│     └─ queries/
│
├─ infra/
│  ├─ docker/
│  │  └─ docker-compose.yml
│  └─ cdk/
│
├─ profiles/
│  ├─ rag-basic.yaml
│  ├─ graph-rag.yaml
│  └─ legal-knowledge-graph.yaml
│
├─ projects/
│  └─ example/
│     └─ project.yaml
│
└─ cli/
```

## 24. CLI構想

最終的には以下の操作を目標とする。

```bash
fde init my-project --profile graph-rag
fde up
fde down
fde validate
fde deploy aws
fde destroy aws
```

## 25. CDK方針

AWS環境はCDK TypeScriptを基本とする。

Stack例:

```text
VpcStack
StorageStack
DatabaseStack
NoSqlStack
SearchStack
GraphStack
AppStack
AgentStack
```

ただし `project.yaml` のenabled設定によって必要Stackのみ生成する。例えば `graph.enabled: false` ならGraphStackを作らない。

## 26. 実装優先順位

### Phase 1

最小ローカルPoC。

```text
Gradio
FastAPI
PostgreSQL
MinIO
OpenSearch
```

Docker Composeで起動。

### Phase 2

Graph対応。

```text
Property Graph:
Neo4j + openCypher

RDF:
Jena + SPARQL
```

project.yamlで切り替え。

### Phase 3

NoSQL対応。

```text
ScyllaDB Alternator
```

DynamoDB互換性を検証。

### Phase 4

GenU Frontend接続。GenUから独自Backend APIへ接続できるようにする。

### Phase 5

AWS CDK。

```text
PostgreSQL → RDS
MinIO → S3
Alternator → DynamoDB
OpenSearch OSS → OpenSearch Service
Neo4j/Jena → Neptune
Local Agent → AgentCore
```

### Phase 6

CLI/Profile化。案件開始時に構成選択だけで環境生成できるようにする。

## 27. 設計原則

### 原則1
DB製品ではなくInterface / Query Languageを基準にする。

```text
Property Graph → openCypher
RDF → SPARQL
Object Storage → S3 API
NoSQL → DynamoDB API
```

### 原則2
AWS固有機能をBackend内部へ閉じ込める。

### 原則3
UIは薄くする。

### 原則4
Search / GraphはSource of Truthにしない。

### 原則5
プロジェクトごとにCapabilityをON/OFFできるようにする。

### 原則6
ローカルOSSとAWS Managedを同じInterfaceで差し替え可能にする。

### 原則7
GenUは可能な限りFrontendを維持し、Backend境界で差し替える。

### 原則8
PoCでは常時課金されるManaged Serviceを最小化する。

## 28. 他AIに依頼したい内容

このドキュメントを入力として、以下を含む実装設計レポートを作成すること。

1. 全体アーキテクチャ
2. コンポーネント責務
3. Repository / Adapter設計
4. project.yaml仕様
5. Profile仕様
6. Docker Compose構成
7. FastAPI Backend構成
8. Gradio UI構成
9. GenU Frontend統合方式
10. PostgreSQL / RDS切替方式
11. ScyllaDB Alternator / DynamoDB切替方式
12. MinIO / S3切替方式
13. OpenSearch OSS / AWS OpenSearch切替方式
14. Neo4j / Neptune openCypher切替方式
15. Jena / Neptune SPARQL切替方式
16. Local Agent / AgentCore切替方式
17. CDK Stack構成
18. CLI設計
19. Source of Truth / Derived Data設計
20. 起動停止・コスト最適化方式
21. セキュリティ設計
22. ログ・監視
23. テスト戦略
24. 段階的な実装ロードマップ

さらに可能なら以下も出力する。

- ディレクトリ構成
- interface定義例
- Docker Compose例
- project.yaml例
- CDK TypeScriptのSkeleton
- FastAPI Skeleton
- Graph Adapter Skeleton
- Storage Adapter Skeleton
- DynamoDB Adapter Skeleton
- README
- ローカル起動手順
- AWSデプロイ手順

## 29. 最終目標

案件ごとに、

```bash
fde init customer-poc --profile graph-rag
fde up
```

だけでローカルPoCを起動し、検証後は、

```bash
fde deploy aws
```

で同じ論理構成をAWSへ展開できること。

また、プロジェクトによって以下を自由に組み合わせられるFDE向け再利用基盤を目指す。

```text
RAGだけ
GraphRAG
RDF Knowledge Graph
SQL Agent
Agent + Tool
GenU UI
Gradio UI
```


---

# 追加設計: LLM / Agent Runtime の切替

## LLM Provider

LLMも他のCapabilityと同様に、ローカルLLMとAWS Bedrockをプロジェクト単位で切り替え可能にする。

```text
LLMService
├─ LocalLLM Adapter
│  ├─ Ollama
│  └─ vLLM
└─ Bedrock Adapter
```

例:

```yaml
llm:
  enabled: true
  provider: local
  engine: ollama
  model: qwen3:8b
  endpoint: http://ollama:11434
```

AWS:

```yaml
llm:
  enabled: true
  provider: bedrock
  model_id: <BEDROCK_MODEL_ID>
  region: ap-northeast-1
```

Agentや業務ロジックからOllama APIやboto3を直接呼ばず、LLMService / Provider Interfaceを経由する。

将来はOpenAI、Anthropic等のProvider追加も可能な設計とする。

### 用途別Model Routing

単一モデル固定ではなく、Planner、回答生成、Embedding、Reranker等を別Provider/Modelへ割り当て可能にする。

```yaml
llm:
  default:
    provider: bedrock
    model_id: <MODEL>

  planner:
    provider: local
    engine: ollama
    model: qwen3:8b

  generation:
    provider: bedrock
    model_id: <MODEL>

  embedding:
    provider: bedrock
    model_id: <EMBEDDING_MODEL>

  reranker:
    enabled: false
```

これにより、軽い分類やPlannerはローカル、重要な生成だけBedrock、といったハイブリッド構成を可能にする。

## Agent Runtime

Agentもローカル専用OSSとAWS AgentCoreを切り替え可能にする。

```text
AgentService
└─ AgentRuntime Interface
   ├─ LocalAgentAdapter
   │  ├─ Strands Agents
   │  ├─ LangGraph
   │  └─ その他OSS
   └─ AgentCoreAdapter
      └─ AWS AgentCore Runtime
```

共通Interfaceイメージ:

```python
class AgentRuntime:
    def invoke(self, request): ...
    def stream(self, request): ...
    def get_capabilities(self): ...
```

Agent定義とRuntimeを分離する。

```text
Agent Definition
├─ system prompt
├─ planner / workflow
├─ tools
├─ memory policy
└─ output contract
       ↓
Local Runtime / AgentCore
```

設定例:

```yaml
agent:
  enabled: true
  runtime: local
  framework: strands
```

AWS:

```yaml
agent:
  enabled: true
  runtime: agentcore
  agent_name: legal-rag-agent
```

## AgentとLLMは独立Capabilityとする

以下の組み合わせを許容する。

| Agent Runtime | LLM Provider | 主用途 |
|---|---|---|
| Local OSS | Local LLM | 完全ローカルPoC |
| Local OSS | Bedrock | Agentはローカル、LLMだけAWS |
| AgentCore | Bedrock | AWS本番寄り |
| AgentCore | その他Provider | 将来拡張 |

つまり `agent.runtime` と `llm.provider` を独立設定とし、Agent Runtimeの選択によってLLM Providerを固定しない。

## 更新後のローカル/AWS対応表

```text
Local / OSS                  AWS / Managed

Gradio / GenU改修UI     →    GenU
FastAPI                 →    ECS/Fargate等
PostgreSQL              →    RDS PostgreSQL
ScyllaDB + Alternator   →    DynamoDB
MinIO                   →    S3
OpenSearch OSS          →    OpenSearch Service
Neo4j + openCypher      →    Neptune + openCypher
Jena/RDF4J + SPARQL     →    Neptune + SPARQL
Ollama / vLLM           →    Bedrock
Strands/LangGraph       →    AgentCore Runtime
```

AWS上でもコスト優先のPoCではOSSコンテナを継続利用できる余地を残す。

## Fully Local Profile例

```yaml
profile: fully-local

ui:
  enabled: true
  type: gradio

agent:
  enabled: true
  runtime: local
  framework: strands

llm:
  enabled: true
  provider: local
  engine: ollama
  model: qwen3:8b

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
  enabled: true
  model: property_graph
  engine: neo4j
  query_language: opencypher
```

## Hybrid Profile例

```yaml
profile: hybrid-poc

ui:
  enabled: true
  type: gradio

agent:
  enabled: true
  runtime: local
  framework: strands

llm:
  enabled: true
  provider: bedrock

storage:
  enabled: true
  engine: s3

search:
  enabled: true
  engine: opensearch
```

## 追加の設計原則

- Agent RuntimeとLLM Providerを独立させる。
- AgentからLLM/DB/Search/Graphの個別SDKを直接呼ばない。
- Tool/Service Interface経由でCapabilityを利用する。
- LLM Provider、Agent RuntimeともFactory/DIで実装を選択する。
- Local AgentはStrands AgentsとLangGraphを優先比較する。
- AWSとの親和性を重視する案件ではStrands Agentsを有力候補とする。
- Ollama/vLLMも必要時のみコンテナ起動可能にする。
- `project.yaml` の `enabled` をDocker Compose/CDKのリソース生成にも反映する。

## 他AIへの追加依頼

既存の設計レポートに加え、以下を具体化すること。

1. AgentRuntime Interface設計
2. Strands/LangGraph/AgentCore Adapter設計
3. LLMProvider Interface設計
4. Ollama/vLLM/Bedrock Adapter設計
5. Agent DefinitionとRuntimeの分離方式
6. Tool Interface設計
7. Agent Runtime × LLM Providerの組み合わせ管理
8. 用途別Model Routing
9. Streaming共通化
10. Error/Retry/Timeout設計
11. Capability Discovery
12. Dependency Injection / Factory設計
13. Local→AWS移行テスト
14. Fully Local / Hybrid / AWS Profile
15. Docker ComposeでのAgent/LLM起動停止
16. CDKでのAgentCore/Bedrock設定
