# Project Schema

`project.yaml` defines the FDE project configuration.

## Root Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `project` | object | yes | Project metadata |
| `profile` | string | yes | Configuration profile |
| `ui` | object | yes | UI settings |
| `database` | object | yes | Database configuration |
| `storage` | object | yes | Storage backend |
| `search` | object | no | Search engine (Phase 2+) |
| `graph` | object | no | Graph database (Phase 3+) |
| `agent` | object | no | Agent framework (Phase 4+) |
| `llm` | object | no | LLM provider (Phase 4+) |
| `redis` | object | no | Redis cache (Phase 4+) |

## project

```yaml
project:
  name: my-rag-app
  description: "RAG application"
  version: "1.0.0"
```

## ui

```yaml
ui:
  enabled: true
  type: gradio  # gradio | streamlit | custom
  port: 7860
  share: false
```

## database.relational

```yaml
database:
  relational:
    enabled: true
    engine: postgresql  # postgresql | sqlite
    host: localhost
    port: 5432
    database: fde
```

## storage

```yaml
storage:
  enabled: true
  engine: minio  # minio | s3
  bucket: documents
  access_key: minioadmin
  secret_key: minioadmin
```

## search

```yaml
search:
  enabled: true
  engine: opensearch  # opensearch | elasticsearch
  url: http://localhost:9200
  index: documents
```

## graph.rdf (Graph Configuration)

Choose ONE graph model per project:

### Option A: Property Graph (Neo4j + openCypher)

```yaml
graph:
  enabled: true

rdf:
  enabled: false
  model: property_graph
  engine: neo4j
  uri: neo4j://localhost:7687
```

### Option B: Semantic Graph (Virtuoso + SPARQL)

```yaml
graph:
  enabled: false

rdf:
  enabled: true
  model: rdf
  engine: virtuoso
  sparql_endpoint: http://localhost:8890/sparql
```

### Option C: Both (Hybrid Graph)

```yaml
graph:
  enabled: true

rdf:
  enabled: true
  model: rdf
  engine: virtuoso
  sparql_endpoint: http://localhost:8890/sparql
```

**Endpoints:**
- Property Graph: `POST /graph/query/cypher`
- RDF Graph: `POST /graph/query/sparql`

## agent

```yaml
agent:
  enabled: true
  runtime: local  # local | remote
  framework: strands  # strands | langgraph | other
```

## llm

```yaml
llm:
  enabled: true
  provider: local  # local | anthropic | openai
  engine: ollama  # ollama | huggingface
  model: qwen3:8b
  base_url: http://localhost:11434
```

## redis

```yaml
redis:
  enabled: true
  host: localhost
  port: 6379
  db: 0
```

## Examples

### rag-basic

```yaml
project:
  name: basic-rag
  version: "1.0.0"

profile: rag-basic

ui:
  enabled: true
  type: gradio

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
  enabled: false

agent:
  enabled: false
```

### graph-rag

```yaml
project:
  name: graph-rag-app
  version: "1.0.0"

profile: graph-rag

ui:
  enabled: true
  type: gradio

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

agent:
  enabled: false
```

### agent-enabled

```yaml
project:
  name: agentic-rag
  version: "1.0.0"

profile: agent-enabled

ui:
  enabled: true
  type: gradio

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

agent:
  enabled: true
  runtime: local
  framework: strands

llm:
  enabled: true
  provider: local
  engine: ollama
  model: qwen3:8b

redis:
  enabled: true
```
