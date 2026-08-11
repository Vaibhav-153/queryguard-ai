# Codebase Guide — How the Files Connect

This guide is meant to help the project owner explain the repository in an interview.

## Entry points

### `app/streamlit_app.py`

Purpose: recruiter/user interface.

Calls:

```text
app/api_client.py
    ↓ HTTP
src/queryguard/api/main.py
```

It does **not** read databases directly. This keeps the hosted UI separate from backend secrets and governance.

### `src/queryguard/api/main.py`

Purpose: FastAPI contract.

Responsibilities:

- health endpoint;
- built-in Chinook `/query` and `/schema` compatibility;
- upload workspace creation;
- workspace query routing;
- document query routing;
- invoice-record endpoint;
- optional `X-QueryGuard-Key` protection.

It delegates business logic rather than generating SQL itself.

## Structured question path

```text
api/main.py
  ↓
services/query_service.py
  ├── analysis/ambiguity.py
  ├── database/schema.py
  ├── retrieval/factory.py
  │    ├── retrieval/lexical.py
  │    └── retrieval/semantic.py
  ├── llm/factory.py
  │    ├── llm/demo.py
  │    ├── llm/ollama.py
  │    ├── llm/gemini.py
  │    └── llm/groq.py
  ├── governance/validator.py
  ├── database/connection.py
  └── analysis/presentation.py
```

### `services/query_service.py`

The orchestration module. It owns the order of operations but not provider/database details.

Input: question + active database path.

Output: `QueryResponse` containing SQL, rows, validation metadata, retrieval evidence, timing, and error state.

### `analysis/ambiguity.py`

Small deterministic checks for questions such as “best customers” without a ranking metric.

It is intentionally limited and does not claim general semantic understanding.

### `database/schema.py`

Reads SQLite metadata and creates:

- `TableSchema`;
- `ColumnSchema`;
- `ForeignKey`.

This is why uploaded SQLite databases do not need hardcoded table names.

### `schema/documents.py`

Converts relational schema objects into text documents used by schema retrieval.

### `retrieval/lexical.py`

BM25-style explainable retrieval baseline. Returns top-K candidate tables.

### `retrieval/semantic.py`

Optional Sentence Transformer retrieval. It is not required for the basic deployment because small schemas often do not justify a vector database.

### `llm/base.py`

Defines the deliberately small interfaces:

- `TextLLM` for generic text completion;
- `SQLGenerator` for SQL generation/repair.

### `llm/sql_generator.py`

Adapts any real `TextLLM` into the SQL-specific interface and applies SQL prompt templates + response cleaning.

### `llm/factory.py`

Maps configuration to Demo/Ollama/Gemini/Groq.

### `llm/prompts.py`

Versionable system/user prompts. Keeping prompts outside provider clients prevents HTTP code and prompt policy from being mixed together.

### `governance/validator.py`

Security boundary based on SQLGlot AST parsing.

Checks:

- exactly one statement;
- SELECT-style root;
- denied operations anywhere in AST;
- referenced database tables;
- active-schema allowlist;
- CTE aliases excluded from physical-table checks.

### `database/connection.py`

Second independent boundary. Opens SQLite using `mode=ro`, sets `PRAGMA query_only=ON`, limits rows, and interrupts long queries.

The validator and read-only connection intentionally overlap: one bug should not automatically mean a writable database.

## Upload path

```text
api/main.py
  ↓
workspaces/manager.py
  ↓
ingestion/*
```

### `workspaces/manager.py`

Central lifecycle module for user uploads.

It:

1. creates a random workspace ID;
2. writes safe basenames only;
3. enforces byte limits;
4. routes by mode;
5. builds SQLite/chunks/invoice artifacts;
6. stores `metadata.json`;
7. deletes expired workspaces.

### `ingestion/common.py`

Shared upload-security helpers: filename cleaning, extension checks, Office ZIP expansion limits.

### `ingestion/sqlite_loader.py`

Runs SQLite `quick_check` and requires at least one user table.

### `ingestion/spreadsheet_loader.py`

Reads `.xlsx`/`.csv`, sanitizes table/column labels, and writes temporary SQLite. This allows spreadsheets to reuse the SQL pipeline.

## Document path

```text
ingestion/pdf_loader.py
     or docx_loader.py
     or pptx_loader.py
        ↓
documents/models.py
        ↓
documents/chunking.py
        ↓
documents/storage.py
        ↓
documents/retrieval.py / semantic.py
        ↓
services/document_service.py
        ↓
llm/factory.py
```

### `ingestion/pdf_loader.py`

Uses PyMuPDF and retains page numbers. If blank pages exist and OCR is installed, it can use OCR.

### `ingestion/docx_loader.py`

Uses `python-docx`; headings become locators, paragraphs/tables become evidence.

### `ingestion/pptx_loader.py`

Uses `python-pptx`; each slide remains a source locator.

### `documents/chunking.py`

Splits long units while preserving provenance. Overlap reduces the chance that a relevant statement is cut exactly at a chunk boundary.

### `services/document_service.py`

Retrieves top-K evidence, builds `[S1]`, `[S2]` blocks, calls the configured LLM, and returns answer + evidence separately.

## Invoice path

```text
workspaces/manager.py
  ↓
invoices/parser.py
  ├── document extraction/OCR
  └── spreadsheet column mapping
  ↓
invoices/database.py
  ↓
invoices.sqlite
```

`invoice_records.json` preserves normalized extraction results; `invoices.sqlite` enables governed aggregation.

## Export path

`export/tabular.py` turns DataFrames into CSV/XLSX bytes and escapes formula-like text before spreadsheet export.

`export/reports.py` creates Markdown/DOCX document-analysis reports.

### `export/reports.py`

Keeps reporting separate from retrieval/LLM logic. It receives an already-validated `DocumentQueryResponse` and only formats the question, answer, and evidence into downloadable bytes/text.

The UI uses these in memory; it does not create permanent exports on the backend.

## Configuration

### `config.py`

Pydantic Settings reads `QUERYGUARD_*` environment variables and `.env` locally.

Secrets use `SecretStr`.

### `.env.example`

Safe template only. Never place real keys in Git.

## Evaluation

### `evaluation/metrics.py`

Contains reusable result matching, Recall@K, mean, percentile helpers.

### `evaluation/runner.py`

Runs Text-to-SQL evaluation against the custom Chinook set.

### `scripts/evaluate_retrieval.py`

Measures schema retrieval separately from LLM generation.

### `scripts/evaluate_document_retrieval.py`

Measures lexical document retrieval on a small synthetic set.

### `scripts/evaluate_invoice_extraction.py`

Measures simple invoice field extraction on transparent synthetic inputs.

## Tests

- `tests/unit/`: deterministic functions, parsing, retrieval, LLM HTTP mocks.
- `tests/integration/`: real Chinook SQLite and workspace creation.
- `tests/security/`: SQL policy attacks and safe controls.
- `tests/api/`: FastAPI behavior, shared key, multipart upload.

## Deployment files

- `Dockerfile`: FastAPI image.
- `Dockerfile.ui`: Streamlit image.
- `docker-compose.yml`: local two-container setup.
- `render.yaml`: hosted FastAPI blueprint.
- `.streamlit/config.toml`: upload/UI server settings.
- `.github/workflows/tests.yml`: CI quality gate.
