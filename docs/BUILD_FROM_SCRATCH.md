# Build From Scratch — How QueryGuard Was Constructed

This chapter is a learning record: if the project had to be rebuilt from an empty repository, this is the order that keeps the work measurable and explainable.

## Phase 0 — Repository foundation

**Goal:** create a Python package that can be cloned and reproduced.

Create:

```text
pyproject.toml
.env.example
.gitignore
src/queryguard/
tests/
scripts/
data/
docs/
```

Why first: configuration, imports, packaging, logging, and tests are easier to fix before AI logic is added.

Acceptance:

```bash
python -m compileall -q src tests scripts
pytest
```

## Phase 1 — Trusted demo data

Use Chinook as a public, understandable relational database.

Build steps:

1. keep an official-source SQL script;
2. verify normalized SQL content using SHA-256;
3. generate SQLite reproducibly;
4. smoke-check known counts/aggregates;
5. document version/license/provenance.

Why: a Text-to-SQL project needs a database whose ground truth is inspectable before introducing a model.

## Phase 2 — Database metadata layer

Implement `database/schema.py` to read:

- tables;
- columns and types;
- primary keys;
- declared foreign keys.

No table names belong in the core query service. The schema object is the contract used by retrieval and governance.

## Phase 3 — Reproducible Text-to-SQL baseline

Add a deterministic demo SQL generator for a few Chinook questions. This is intentionally not called AI.

Pipeline:

```text
question -> SQL candidate -> SQLite result
```

Why: it lets API/database control flow be tested without a model download or API key.

## Phase 4 — SQL governance before real LLMs

Add SQLGlot parsing and a separate read-only SQLite executor.

Policy:

```text
one statement
+ SELECT-style root
+ denied AST operations absent
+ physical tables in active allowlist
```

Then independently enforce:

```text
SQLite mode=ro
PRAGMA query_only=ON
row cap
timeout
```

Why: a prompt telling the model to be safe is not an execution boundary.

## Phase 5 — Schema retrieval and evaluation

Convert each table schema into a retrieval document. Implement the BM25-style baseline before embeddings.

Create an evaluation JSONL containing:

```text
question
gold SQL
required tables
order sensitivity/category
```

Measure Recall@K independently from LLM answer quality.

Only after the baseline exists, add optional Sentence Transformer semantic retrieval.

## Phase 6 — Real LLM adapters

Create the small `TextLLM.complete()` interface and implement:

- Ollama for local inference;
- Gemini for hosted demo;
- Groq as optional alternative.

Wrap it with `LLMSQLGenerator` so SQL-specific prompts/cleanup are not duplicated inside provider HTTP clients.

Never put provider secrets in source code.

## Phase 7 — Orchestration and bounded failure handling

`QueryService` owns order, not low-level implementation:

```text
clarify -> retrieve -> prompt -> generate -> validate -> execute -> present
```

Ordinary generation/execution errors may receive one repair attempt. Security-policy failures are returned immediately.

Record retrieval/generation/validation/execution latency separately.

## Phase 8 — FastAPI contract

Add:

```text
GET /health
GET /schema
POST /query
```

Use Pydantic request/response models. Test the API with the demo provider. The API should delegate to services rather than contain SQL logic.

## Phase 9 — Dynamic source workspaces

The original project becomes reusable by adding server-generated workspace IDs.

Workspace lifecycle:

```text
upload -> sanitize -> validate -> ingest -> metadata -> query -> expiry/delete
```

The built-in Chinook demo remains untouched.

Security controls added here:

- file count/size/combined-size limits;
- safe basenames;
- extension allowlists;
- Office ZIP expansion limits;
- SQLite integrity checks;
- workspace TTL;
- no arbitrary request filesystem paths.

## Phase 10 — Excel and CSV

Do not build a second natural-language analytics engine.

```text
XLSX/CSV -> pandas -> temporary SQLite -> existing QueryGuard SQL pipeline
```

This reuses schema retrieval, SQLGlot, read-only execution, evaluation concepts, and downloads.

## Phase 11 — Document RAG

Structured SQL and unstructured text have different abstractions.

For PDF/DOCX/PPTX:

1. parse source-aware text units;
2. preserve page/section/slide locator;
3. chunk long units with overlap;
4. retrieve top-K evidence;
5. build evidence labels `[S1]`, `[S2]`;
6. ask the LLM to use only evidence;
7. return answer and evidence separately.

Add optional OCR only for scanned/image-only sources.

## Phase 12 — Invoice hybrid mode

Invoice data has two useful representations:

```text
normalized fields -> SQLite analytics
raw extracted text -> RAG evidence
```

Start with transparent labels/regex/column aliases and `needs_review`. Do not claim production invoice accuracy without a representative labeled set.

## Phase 13 — Streamlit UI and downloads

The UI should teach the architecture while it is used.

Modes:

```text
Try Demo
Database
Spreadsheet
Documents
Invoices
```

For SQL, display retrieved schema, SQL, governance, rows/chart, latency, and downloads. For documents, display cited sources. For invoices, display normalized fields/review flags and analytics/document tabs.

Keep API/provider secrets out of browser-facing code.

## Phase 14 — Testing and component evaluation

Run software checks separately from AI-quality evaluation.

Software:

```text
Ruff
compile
unit
integration
API
security
ingestion
workspace
```

Quality:

```text
schema Recall@K
document Hit@K
invoice extraction exact match
Text-to-SQL execution match (real model experiment)
```

A test passing does not mean an LLM answer is correct.

## Phase 15 — Deployment and documentation

Add Docker/Compose, GitHub Actions, Render Blueprint, Streamlit secrets template, build verification, architecture/codebase/theory/data/security/testing/interview guides.

Deployment is complete only after a fresh environment can install, rebuild/verify Chinook, run tests, start the API/UI, and keep secrets outside Git.

## How to explain this build order in an interview

> I built the deterministic data and security boundaries first, then established retrieval/evaluation baselines, and only then added real LLM providers. After the core Text-to-SQL pipeline was measurable, I generalized the data source with temporary workspaces and reused the same governed SQL path for spreadsheets. Unstructured documents received a separate RAG path, while invoices combine structured fields and document evidence. I avoided agents/microservices because they were not required for the problem.
