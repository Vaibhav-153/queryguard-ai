# Architecture

## System boundaries

QueryGuard is a modular monolith. This is intentional: one graduate developer can understand the complete request path without distributed-system overhead.

```mermaid
flowchart TD
    Client --> FastAPI
    FastAPI --> Ambiguity
    Ambiguity --> Retriever
    Retriever --> PromptBuilder
    PromptBuilder --> Ollama
    Ollama --> Validator
    Validator -->|approved| Executor
    Validator -->|security rejection| Response
    Executor --> SQLite
    SQLite --> Presenter
    Presenter --> Response
```

## Component responsibilities

- `database/schema.py`: discovers live tables, columns and foreign keys.
- `schema/documents.py`: turns schema objects into retrieval documents.
- `retrieval/lexical.py`: explainable ranking baseline.
- `retrieval/semantic.py`: embedding-based Top-K retrieval.
- `llm/ollama.py`: minimal HTTP client; no agent framework.
- `governance/validator.py`: SQLGlot AST policy enforcement.
- `database/connection.py`: independent read-only database safety boundary.
- `analysis/ambiguity.py`: narrow deterministic clarification rules.
- `services/query_service.py`: orchestration and one bounded repair attempt.
- `evaluation/runner.py`: end-to-end result execution comparison.

## Request sequence

```mermaid
sequenceDiagram
    participant U as User
    participant Q as QueryService
    participant R as Retriever
    participant L as LLM
    participant V as Validator
    participant D as SQLite

    U->>Q: natural-language question
    Q->>Q: ambiguity check
    Q->>R: retrieve Top-K tables
    R-->>Q: ranked schema context
    Q->>L: question + schema
    L-->>Q: SQL candidate
    Q->>V: parse and validate
    alt security violation
        V-->>Q: block
        Q-->>U: controlled rejection
    else valid query
        Q->>D: execute read-only
        D-->>Q: database rows
        Q-->>U: SQL + rows + metadata
    else ordinary error
        Q->>L: one repair request
    end
```

## Storage

V1 uses a local SQLite file plus JSON/JSONL evaluation artifacts. It does not need PostgreSQL, Redis, object storage, or a vector database at Chinook scale.

## Failure handling

- incomplete/vague question -> clarification;
- LLM unavailable -> controlled `error` response;
- destructive/multi-statement SQL -> `blocked`, no repair;
- unknown table/parse/execution error -> at most one repair;
- timeout -> controlled database error;
- empty valid result -> successful response with zero rows.

## Production evolution

A real internal deployment would add an authenticated identity, per-user dataset permissions, row/column policies, audit retention, connection pooling, workload limits, database-specific statement timeouts, model/prompt version tracking, and monitored evaluation sets before adding distributed infrastructure.
