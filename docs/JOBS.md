# Jobs — ジョブ実行基盤

スクレイピング・前処理・RAG シードなどのバッチ処理を載せるための汎用の仕組み。
雛形には具体的なジョブは含まれず、サンプル `hello` と `hello-pipeline` だけがある（削除可）。

設計判断: [ADR 004](../adr/004-job-execution.md)（実行基盤）、[ADR 003](../adr/003-rag-data-layers.md)（RAG 文書台帳）

---

## 1. ジョブを追加する

`backend/jobs/definitions/` に 1 ファイル追加する（このパッケージ内のモジュールは自動で読み込まれる）。

```python
# backend/jobs/definitions/my_job.py
from typing import Any

from backend.jobs.base import Job
from backend.jobs.context import JobContext
from backend.jobs.registry import register_job


@register_job("my-job")
class MyJob(Job):
    description = "何をするジョブか"

    async def run(self, ctx: JobContext) -> dict[str, Any]:
        limit = int(ctx.params.get("limit", 100))          # params は読み取り専用
        ctx.logger.info("start", limit=limit)               # 標準出力へ（CloudWatch に流れる）
        uri = ctx.artifacts.put_json("items.json", [...])  # s3://<bucket>/runs/<root_run_id>/my-job/items.json
        return {"count": 0, "items_uri": uri}               # 小さな要約だけ返す（job_runs.result に保存）
```

別パッケージに置きたい場合は `JOB_MODULES=backend.jobs.definitions,myproject.jobs` のように追加する。

### 守ること（AWS へそのまま持っていくための約束）

| 約束 | 理由 |
|---|---|
| ジョブ間のデータは `ctx.artifacts`（S3/MinIO）経由。ローカルディスクに残さない | ECS タスクはステップごとに別コンテナ |
| 設定は環境変数（`Settings`）か `params` | ECS TaskDefinition / Secrets Manager にそのまま写る |
| ログは標準出力（`ctx.logger`） | CloudWatch Logs |
| 失敗は例外で返す（終了コード 1） | 状態はプロセス終了から判定される |
| 同じ params で再実行しても壊れない（冪等） | Step Functions の Retry、手動再実行 |
| ステータスを自分で書かない | 実行基盤のイベントで更新される（ADR 004） |

### `JobContext`

| 属性 | 内容 |
|---|---|
| `run_id` / `job_name` / `parent_run_id` | 実行 ID。パイプライン内なら `parent_run_id` はパイプラインの run |
| `params` | 読み取り専用の dict |
| `artifacts.put_bytes / put_json(name, ...)` | `runs/{root_run_id}/{job_name}/{name}` に保存し `run_artifacts` に記録。URI を返す |
| `artifacts.get_bytes / get_json(uri)` | 読み出し |
| `artifacts.find_upstream(name, job_name=None)` | 同じパイプライン実行の前段ステップが出力した成果物の URI |
| `session_factory()` | DB セッション（台帳 `CatalogRepository` などに使う） |
| `logger` | `run_id` / `job` を束縛した structlog ロガー |

### RAG 取り込みジョブを書く場合

文書は `CatalogRepository`（`backend/repositories/catalog.py`）に登録する。

```python
from backend.repositories.catalog import CatalogRepository

db = ctx.session_factory()
try:
    catalog = CatalogRepository(db)
    result = catalog.upsert_document(
        doc_id, source_uri, content_hash, targets=["opensearch"],
        run_id=ctx.run_id, raw_uri=raw_uri, processed_uri=processed_uri,
    )
    # result.changed が False なら内容は変わっていない（再インデックス不要）
    for doc in catalog.find_by_target_status("opensearch", "pending"):
        ...  # インデックス後に catalog.mark_target(doc.id, "opensearch", "indexed", run_id=ctx.run_id)
finally:
    db.close()
```

大量のキー単位データ（例: クロール済み URL の重複排除）は台帳ではなく NoSQL（Scylla / DynamoDB）を使う。

---

## 2. パイプラインを定義する

`backend/jobs/pipelines/*.yaml`（`JOB_PIPELINES_DIR`）。1 ステップ = AWS の Step Functions の 1 Task state。

```yaml
name: rag-ingest
description: 取得 → 前処理 → インデックス
schedule: "cron(0 18 * * ? *)"     # AWS EventBridge Scheduler 用（ローカルでは無視）
steps:
  - id: fetch                      # 省略時は job 名。パイプライン内で一意
    job: my-fetch-job
    params: { source: example }
    timeout_seconds: 3600          # → TimeoutSeconds（ローカルでは kill）
    retries: 2                     # → Retry
    resources: { cpu: 1024, memory: 2048 }  # → ECS タスクサイズ（AWS のみ）
  - id: index
    job: my-index-job
```

ステップは前から順に実行され、1 つでも失敗するとそこで止まり、パイプラインの run は `failed` になる。
実行時に `overrides`（`{"<step id>": {params}}`）でステップの params を上書きできる。

---

## 3. 実行する（ローカル）

```bash
make jobs                                   # 登録済みジョブとパイプライン一覧
make job name=hello params='{"name":"x"}'   # 単発実行（完了まで待つ）
make pipeline name=hello-pipeline           # パイプライン実行
make job-runs                               # 最近の実行
uv run python -m backend.jobs status <run_id>
make job-docker name=hello                  # コンテナで実行（ECS RunTask 相当）
```

API（backend 起動時）:

| Method | Path | 説明 |
|---|---|---|
| GET | `/jobs/` | 登録済みジョブ |
| POST | `/jobs/{job}/runs` | 非同期起動（202, `{"run_id"}`）。body: `{"params": {...}}` |
| GET | `/jobs/runs?job_name=&status=&limit=` | 実行一覧（新しい順） |
| GET | `/jobs/runs/{run_id}` | 詳細（result / error / artifacts / 子 run） |
| GET | `/jobs/pipelines` | パイプライン定義 |
| POST | `/jobs/pipelines/{name}/runs` | パイプライン起動（ローカルのみ。AWS では 501） |

状態: `pending → running → succeeded | failed`。

成果物用のバケット（`MINIO_BUCKET`, 既定 `knowledge-root`）は compose の `minio-init` が作成する
（AWS では CDK が S3 バケットを作る。アプリはバケットを作らない）。`make up` を使わずに MinIO を
起動した場合は `docker compose -f infra/docker-compose.yml up minio-init` を一度実行する。

---

## 4. 仕組み

```
launch()                         exec（ジョブ本体プロセス）
  │ job_runs に pending を作成       │ params を job_runs から読む
  │ プロセス/タスク起動 ─────────────▶│ Job.run(ctx)
  │                                  │ result / artifacts を保存（データ）
  │ ◀──────────── 終了コード ─────────┘
  ▼
RunEvent(started / succeeded / failed) → RunEventHandler → job_runs.status
```

| ファイル | 役割 |
|---|---|
| `backend/jobs/base.py` | `Job` ABC |
| `backend/jobs/registry.py` | `@register_job`, `discover_jobs` |
| `backend/jobs/context.py` | `JobContext`, `ArtifactStore` |
| `backend/jobs/executor.py` | ジョブ本体の実行（`exec` サブコマンド） |
| `backend/jobs/events.py` | `RunEvent`, `RunEventHandler`（状態更新の唯一の入口） |
| `backend/jobs/launcher.py` | `JobLauncher` ABC, `LocalJobLauncher` |
| `backend/jobs/pipeline.py` | YAML 読み込み, `LocalPipelineRunner` |
| `backend/jobs/aws.py` | `EcsJobLauncher`, ECS イベント変換, `lambda_handler` |
| `backend/jobs/__main__.py` | CLI |
| `backend/repositories/job_run.py` | `job_runs` / `run_artifacts` |
| `backend/storage/object_store.py` | S3 API（MinIO / S3） |

---

## 5. AWS へ移す

設定:

```bash
JOB_LAUNCHER=ecs
STORAGE_ENGINE=s3
ECS_CLUSTER=...
ECS_JOB_TASK_DEFINITION=...      # backend と同じイメージ、コンテナ名は ECS_JOB_CONTAINER_NAME
ECS_SUBNETS=subnet-a,subnet-b
ECS_SECURITY_GROUPS=sg-xxx
```

- 単発ジョブ: `EcsJobLauncher` が `run_task(startedBy=<run_id>, command=exec ...)` を呼ぶ。
- 状態: EventBridge ルール（`source=aws.ecs`, `detail-type=ECS Task State Change`, 対象クラスタ）→
  Lambda `backend.jobs.aws.lambda_handler`（VPC 内、RDS に接続）。
- パイプライン: YAML から Step Functions（`ecs:runTask.sync`）を生成し、`schedule` は EventBridge Scheduler。
  各ステップの子 run は state machine 側で `job_runs` を作成してから RunTask する。

**未実装（CDK）**: Job 用 TaskDefinition、EventBridge ルール + Lambda、YAML → Step Functions 生成、Scheduler。
アプリ側のコード（`EcsJobLauncher`, `lambda_handler`）はこれらが揃えば変更なしで動く想定。
