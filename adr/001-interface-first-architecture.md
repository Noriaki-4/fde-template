# ADR 001: Interface-First Architecture

## Status
Accepted

## Context

FDE PoC 基盤は複数の DB 製品（PostgreSQL / RDS、Neo4j / Neptune、OpenSearch など）とローカル / AWS の複数構成に対応する必要がある。Database 製品に依存しない設計により、以下を実現する：

1. 同じアプリケーションコードで複数環境での動作
2. プロジェクトごとの構成選択が容易
3. 将来の DB 変更に対応可能

## Decision

**Database 製品ではなく、標準インターフェース / クエリ言語を基準にする。**

### 採用インターフェース

| Capability | インターフェース | 理由 |
|-----------|-------------|------|
| Property Graph | openCypher | Neo4j / Neptune 共通サポート |
| RDF | SPARQL | Jena / Neptune 共通サポート |
| Object Storage | S3 API | MinIO / S3 互換 |
| NoSQL | DynamoDB API | ScyllaDB Alternator / DynamoDB 互換 |
| Relational | SQL | PostgreSQL / RDS 互換 |

### 実装パターン

```python
# Service 層（ビジネスロジック）
class GraphService:
    def get_neighbors(self, node_id: str) -> List[dict]:
        pass

# Repository 層（データアクセス）
class GraphRepository(ABC):
    @abstractmethod
    def query(self, query: str) -> List[dict]:
        pass

# Adapter 層（製品固有実装）
class Neo4jGraphRepository(GraphRepository):
    def query(self, query: str) -> List[dict]:
        # openCypher で実装
        pass

class NeptuneGraphRepository(GraphRepository):
    def query(self, query: str) -> List[dict]:
        # openCypher で実装
        pass
```

### 設定による切り替え

```yaml
# project.yaml
graph:
  enabled: true
  engine: neo4j          # or neptune
  query_language: opencypher
```

## Consequences

### Good
- 単一の Service コード → 複数環境で動作
- DB 製品変更が容易（Config だけ）
- テストで Mock / 別製品に置き換え可能
- 将来の DB 追加が容易

### Bad
- Adapter 実装の負荷増加
- DB 製品固有機能の利用が制限される
- openCypher / SPARQL 習熟が必要

### Mitigation
- Adapter で製品固有機能も公開（共通 API + 拡張機能）
- ドキュメント充実化
- Reference Implementation 提供

## Alternatives Considered

### A. Database Driver Abstraction
各 DB driver を直接抽象化。

**問題**: クエリ言語が異なるため困難（Cypher vs SPARQL vs SQL）

### B. ORM / Query Builder
SQLAlchemy / Strawberry GraphQL など既存ツール活用。

**問題**: 複数言語（SQL + Cypher + SPARQL）に対応するツールが無い

### C. ノーマライズド中間形式
Canonical Graph → 各 DB へ変換。

**選択**: 中間層として採用（14. Graphの中間形式参照）

## Related

- [002-local-aws-parity](002-local-aws-parity.md)
- [IMPLEMENTATION_PLAN.md - 設計原則1](../IMPLEMENTATION_PLAN.md#設計原則)
