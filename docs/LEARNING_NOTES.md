# Learning Notes and Ownership Checklist

Do not memorize the README only. Be able to explain the code path.

## Phase 1 — Python project structure

Understand:

- `pyproject.toml`;
- editable install;
- package under `src/`;
- environment variables;
- Pydantic settings.

Mini assignment: add one harmless configuration field such as a UI message and read it through `Settings`.

## Phase 2 — SQLite

Understand:

- URI `mode=ro`;
- primary/foreign keys;
- `sqlite_master`;
- `PRAGMA table_info`;
- `PRAGMA foreign_key_list`;
- `PRAGMA quick_check`;
- query-only mode.

Mini assignment: write a script that prints all tables and primary keys from Chinook without using QueryGuard helpers.

## Phase 3 — Retrieval

Understand:

- tokens;
- term frequency;
- document frequency;
- inverse document frequency;
- top-K;
- Recall@K;
- lexical vs semantic retrieval.

Mini assignment: add one transparent query-expansion synonym and rerun retrieval metrics. Keep the change only if it solves a real failure without hurting others.

## Phase 4 — LLM prompting

Understand:

- system vs user prompt;
- temperature/determinism;
- schema context;
- why output cleanup is not a security boundary;
- local vs hosted inference.

Mini assignment: compare two prompts on a development subset and record result in `PROJECT_DECISIONS.md`.

## Phase 5 — SQL governance

Understand:

- AST;
- CTE;
- physical vs alias table;
- denied operations;
- defense in depth.

Mini assignment: add a security test for another unsupported statement and explain why it is blocked.

## Phase 6 — Upload/workspaces

Understand:

- path traversal;
- safe basename;
- random workspace ID;
- temporary storage;
- expiry;
- why QueryService is created per active database path.

Mini assignment: add a test that uploads a filename containing `../` and verify it cannot escape the workspace.

## Phase 7 — documents/RAG

Understand:

- parser → unit → chunk → retrieval → prompt → evidence;
- chunk overlap;
- source provenance;
- prompt injection.

Mini assignment: add one synthetic document chunk/question where lexical retrieval fails and test semantic retrieval if your machine can run it.

## Phase 8 — invoices

Understand:

- structured vs semi-structured data;
- regex/label extraction;
- nullable fields;
- manual review;
- why 100% synthetic accuracy is not a production claim.

Mini assignment: add a new invoice label alias and a failing/passing regression test.

## Phase 9 — deployment

Understand:

- frontend/backend split;
- environment secrets;
- health checks;
- Render `$PORT`;
- Streamlit secrets;
- free-service cold starts;
- ephemeral workspace limitation.

## Before an interview

You should be able to draw from memory:

1. structured pipeline;
2. document pipeline;
3. invoice hybrid pipeline;
4. security boundaries;
5. evaluation layers.

If you cannot explain a module, read `CODEBASE_GUIDE.md` and then open the actual source file.
