# ADR 002: Local ↔ AWS Parity

## Status
Accepted

## Context

FDE PoC は開発効率のため **ローカル開発から AWS デプロイまで同じコードで動作** すべき。ただし、ローカル（OSS）と AWS Managed Service では：

- 機能差がある（e.g., Neptune は openCypher のみ、Bedrock は API 応答形式が異なる）
- 性能特性が異なる
- 起動速度が異なる（Managed Service はウォームアップ時間）

## Decision

**Adapter / DI パターンで実装差を吸収。設定ファイル（project.yaml）で動作環境を切り替え可能にする。**

### 対応表

| Layer | Local | AWS |
|-------|-------|-----|
| **UI** | Gradio | GenU / CloudFront |
| **Backend** | FastAPI | ECS Fargate / Lambda |
| **Database** | PostgreSQL 16 | RDS PostgreSQL |
| **NoSQL** | ScyllaDB Alternator | DynamoDB |
| **Storage** | MinIO | S3 |
| **Search** | OpenSearch OSS | OpenSearch Service |
| **Graph** | Neo4j 5.26 | Neptune |
| **LLM** | Ollama | Bedrock |
| **Agent** | Strands / LangGraph | AgentCore Runtime |
| **Jobs** | subprocess / `docker compose run` | ECS Fargate RunTask + Step Functions（ADR 004） |
| **IaC** | Docker Compose | AWS CDK |

### 実装方法

```python
# Factory パターン
class StorageFactory:
    @staticmethod
    def create(config: dict) -> Storage:
        if config['engine'] == 'minio':
            return MinIOStorage(config)
        elif config['engine'] == 's3':
            return S3Storage(config)

# 設定ファイル
class Config:
    @classmethod
    def from_yaml(cls, path: str) -> 'Config':
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls(data)
```

### project.yaml 例（ローカル）

```yaml
storage:
  enabled: true
  engine: minio
  config:
    endpoint: minio:9000
    bucket: knowledge-root

database:
  relational:
    enabled: true
    engine: postgresql
    config:
      url: postgresql://localhost/fde_poc

graph:
  enabled: true
  engine: neo4j
  config:
    uri: bolt://neo4j:7687
```

### project.yaml 例（AWS）

```yaml
storage:
  enabled: true
  engine: s3
  config:
    bucket: fde-knowledge-bucket
    region: ap-northeast-1

database:
  relational:
    enabled: true
    engine: rds
    config:
      url: postgresql://rds.example.com/fde_prod

graph:
  enabled: true
  engine: neptune
  config:
    endpoint: neptune.example.com:8182
    region: ap-northeast-1
```

## Consequences

### Good
- 開発環境で本番環境と同じコードで検証可能
- CI/CD での環境切り替えが Config Only
- コンテナ起動 / AWS デプロイの一貫性
- エンジニアの学習曲線が短い

### Bad
- 全環境でテスト必須（Local + AWS）
- AWS IAM / VPC 設定の複雑性
- Managed Service の初期化時間がテストを遅延させる

### Mitigation
- Local integration test → AWS staging test → Production の段階的検証
- AWS CodeBuild で自動テスト
- 設定ファイルのバリデーション強化

## Alternatives Considered

### A. ローカルのみ対応
AWS は別途実装。

**問題**: コード重複、デプロイ時のトラブル多発

### B. AWS 前提、ローカルは LocalStack で再現
LocalStack（AWS エミュレータ）を使用。

**問題**: LocalStack が重く開発効率低下、すべての AWS サービス未対応

### C. マイクロサービス化
各コンポーネント独立デプロイ。

**問題**: PoCには複雑すぎる、デプロイ負荷増加

## Related

- [001-interface-first-architecture](001-interface-first-architecture.md)
- [RUNBOOK.md - デプロイ手順](../RUNBOOK.md)
- [IMPLEMENTATION_PLAN.md - Phase 5](../IMPLEMENTATION_PLAN.md#phase-5-aws-cdk-実装-week-8-9)
