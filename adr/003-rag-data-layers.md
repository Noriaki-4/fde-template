# ADR 003: RAG データの 3 層化と文書台帳（Document Catalog）

## Status
Accepted

## Context

これまで RAG の文書メタデータの置き場が決まっていなかった。

- `documents` テーブル（Postgres）が本文・タイトル・メタデータを持ち、`SearchService` がそこを LIKE 検索している。
- OpenSearch は `content` とメタデータを独自インデックスに持ち、Postgres とは無関係。
- Neo4j / RDF にも別途データが入る。

この状態では次のことができない。

- 文書の削除・更新を複数の検索ストア（OpenSearch / Neo4j / RDF）へ確実に伝搬する
- コンテンツハッシュによる重複・差分検出
- 「どの取り込み実行（run）がどの文書を作ったか」の追跡と、run 単位の取り消し・再生成
- 派生ストアの再構築

## Decision

RAG データを 3 層に分け、**メタデータとリネージの正本は Postgres の文書台帳** とする。

| 層 | 中身 | Local → AWS | 位置づけ |
|---|---|---|---|
| 原本 | 取得した生データ・前処理済みテキスト | MinIO → S3 | 内容の正本 |
| **文書台帳** | doc_id, source_uri, content_hash, version, raw/processed URI, ingest_run_id, ACL, 状態, ストア別同期状態 | **Postgres → RDS / Aurora PostgreSQL** | メタデータの正本 |
| 派生ストア | チャンク + 埋め込み、エンティティ・関係 | OpenSearch / Neo4j / Virtuoso → 各 Managed | 検索用の複製。原本 + 台帳から再構築可能 |

実装:

- `catalog_documents` — 文書 1 件 1 行。`content_hash` が同じなら upsert は no-op、変われば `version` を上げる。
- `catalog_document_targets` — (文書, 派生ストア) ごとの同期状態
  `pending | indexed | failed | pending_delete | deleted` と `indexed_version`。
  インデックス作成ジョブは `find_by_target_status("opensearch", "pending")` で処理対象を得る。
- `CatalogRepository`（`backend/repositories/catalog.py`）。
- `ingest_run_id` / `last_run_id` は `job_runs.id`（ADR 004）を参照する。run と台帳が同じ DB にあるため、run 単位の取り消し・再生成をトランザクションで整合させられる。

### なぜ Postgres か（「既にあるから」ではない理由）

- 書き込みは取り込み時のみで低頻度。DynamoDB の書き込みスケールの利点が生きない。
- 読みは「ストア × 状態」の絞り込み、run → 文書の結合、ACL など、関係操作が中心。
- 派生ストアは複数あり、どれもトランザクションを持たない。正本はそれらの外側に要る。

### 採用しなかった案

- **OpenSearch を正本にする**: トランザクションがなく、Neo4j / RDF への伝搬管理ができない。
- **S3 のサイドカー `.metadata.json` のみ**（Bedrock Knowledge Bases 方式）: 単一ストアなら簡潔だが、複数ストアの同期状態やリネージを持てない。将来 Bedrock KB に移る場合は台帳からサイドカーを書き出せばよい。
- **DynamoDB / ScyllaDB**: 上記のアクセスパターンに合わない。NoSQL は「ジョブ固有の大量 KV データ」（例: クロール済み URL）の置き場とする。

## Consequences

- 既存の `documents` テーブル + `SearchService`（Postgres LIKE 検索）は、OpenSearch 無効時の簡易検索として **当面そのまま残す**。台帳とは別物であり、本文は将来 S3 に、検索は OpenSearch に寄せる（移行は別タスク）。
- 台帳の読み取り API はまだない（ジョブから `CatalogRepository` を直接使う）。必要になったら `/catalog/*` を追加する。
