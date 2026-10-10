# ADR 004: ジョブ実行基盤（AWS から逆算したローカル構成）

## Status
Accepted

## Context

スクレイピング・前処理・RAG シードなどのバッチ処理を **将来** 追加できるよう、雛形として
汎用のジョブ実行の仕組みが必要。要件:

- ローカルで動く
- AWS へ移行しやすい（AWS のジョブ管理から逆算してローカル構成を決める）
- 具体的なジョブは雛形に含めない（サンプル `hello` のみ）

## Decision

### AWS の姿（正）

```
EventBridge Scheduler ─┐
API / CLI ─────────────┼─▶ Step Functions（パイプライン, ecs:runTask.sync）
                       │       └─▶ ECS Fargate Task: python -m backend.jobs exec <job> --run-id <id>
                       └─▶ ECS RunTask（単発ジョブ）
ECS Task State Change ─▶ EventBridge ─▶ Lambda(backend.jobs.aws.lambda_handler) ─▶ job_runs (RDS)
```

- 実行単位は **ECS Fargate RunTask**。Lambda は 15 分制限・依存サイズで不向き。backend と同じイメージを使う。
- パイプラインは **Step Functions**。YAML の 1 ステップ = 1 Task state（timeout → TimeoutSeconds、retries → Retry、resources → cpu/memory）。
- スケジュールは **EventBridge Scheduler**（YAML の `schedule`）。
- 不採用: AWS Batch（GPU / キューが要るまで不要。Step Functions から呼べるので後で差替可）、MWAA/Airflow（PoC には重い）、Celery/RQ（AWS Managed に写像しない）。

### ローカル（AWS の縮小コピー）

| 関心事 | AWS | Local |
|---|---|---|
| 実行 | ECS RunTask | `LocalJobLauncher`（subprocess）/ `docker compose --profile jobs run` |
| コマンド | `python -m backend.jobs exec <job> --run-id <id>` | 同一 |
| 中間データ | S3 `runs/{root_run_id}/{job}/` | MinIO 同一パス |
| パイプライン | Step Functions | `LocalPipelineRunner`（同じ YAML を逐次実行） |
| 状態更新 | ECS イベント → Lambda → `RunEventHandler` | プロセス開始/終了 → `RunEventHandler` |
| 実行記録 | RDS PostgreSQL | Postgres |

### 状態はジョブに書かせない

ジョブ自身がステータスを書く方式だと、OOM kill やタイムアウトで「running のまま」残る。
そのため **ステータスは実行基盤からのイベントだけで更新** する（`RunEvent` → `RunEventHandler`
→ `JobRunRepository.apply_status`）。ジョブが書くのは結果（result / artifacts）というデータのみ。
`apply_status` は冪等で、終了状態は上書きしない（重複・順不同のイベント配送に耐える）。

### データの持ち主

| データ | 持ち主 |
|---|---|
| 実行状態（真実） | 実行基盤（ECS / Step Functions）。`job_runs` はその射影 |
| 実行記録・リネージ | Postgres（`job_runs`, `run_artifacts`。ADR 003 の文書台帳と結合） |
| ジョブ固有データ | 各ジョブが選ぶ（大量 KV なら NoSQL = Scylla / DynamoDB） |

`job_runs` を DynamoDB / Scylla にしないのは、一覧・絞り込み・親子（パイプライン）・台帳との結合が
中心のリレーショナルなデータだから。

## Consequences

- 実装済み: `backend/jobs/`（Job ABC, registry, context, executor, events, launcher, pipeline, aws, CLI）、
  `/jobs/*` API、`job_runs` / `run_artifacts`、compose の `jobs` プロファイル、`EcsJobLauncher` と ECS イベント変換。
- **未実装（AWS 化の残作業）**: CDK での Job 用 TaskDefinition、YAML → Step Functions 生成、
  EventBridge ルール + Lambda、Scheduler。`EcsJobLauncher` / `lambda_handler` はこれらが揃えば動く形にしてある。
- AWS ではパイプラインを API から起動しない（`/jobs/pipelines/*/runs` は 501）。Step Functions の StartExecution を使う。
- 同一パイプラインの多重起動防止は未実装（必要時に Postgres の一意制約 / advisory lock で追加）。
