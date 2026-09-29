# Architecture

QueryGuard AI keeps the LLM away from direct database access. Model output is treated as untrusted text until it passes the SQL validator.

## Structured-data flow

```text
Question
  |
  v
Schema extraction
  |
  v
Lexical table retrieval
  |
  v
LLM SQL generation
  |
  v
SQLGlot validation
  |
  v
Read-only SQLite execution
  |
  v
Rows + validation metadata
```

`queryguard.query_service.QueryService` coordinates this flow. Schema retrieval selects likely tables and also adds directly related tables when foreign keys indicate a relationship.

### Validation boundaries

`queryguard.sql_guard` parses the generated statement and applies these rules:

- exactly one statement;
- SELECT-style root only;
- no DDL/DML or administrative nodes;
- physical table references must be present in the discovered schema;
- CTE names are not mistaken for physical tables.

SQLGlot is a required runtime dependency. A conservative fallback exists only so a missing dependency fails toward a narrower set of accepted SQL during troubleshooting.

`queryguard.database` then opens SQLite with `mode=ro` and `PRAGMA query_only = ON`. A progress handler interrupts queries that exceed the configured timeout, and only a configured number of rows are returned.

## Uploaded structured data

SQLite uploads are integrity-checked before a workspace is created. CSV and XLSX files are converted into a temporary SQLite database. Sheet and column names are normalized before insertion.

Workspaces have random identifiers, configured size limits, and an expiration timestamp. Runtime workspace directories are excluded from Git.

## Document flow

PDF, DOCX and PPTX files are converted into text chunks. PDF pages with no extractable text can use OCR when `pytesseract` and Tesseract are available.

The document retriever uses lexical term overlap after removing common stopwords. The answer generator receives only retrieved passages, and the API returns source filename, locator and excerpt with the answer.

## Invoice flow

CSV and XLSX invoices use column aliases for fields such as invoice number, date, vendor, customer, currency and total. PDF/image invoices use conservative regular-expression extraction after text extraction or OCR.

Every invoice record includes `needs_review`. Extracted records are also written to a temporary SQLite table so the same governed query pipeline can be used for analysis.

## Interfaces

The FastAPI application is defined in `queryguard.api`. The Streamlit client in `app/streamlit_app.py` calls the API rather than importing database services directly.

An optional `X-QueryGuard-Key` protects API endpoints when `QUERYGUARD_API_ACCESS_KEY` is configured.

## Provider adapters

The package contains small adapters for Gemini, Groq and Ollama plus a deterministic demo provider. Provider selection and model names are configured through environment variables.

The demo provider exists for repeatable local tests. It recognizes the bundled example questions and otherwise returns a small table preview; it is not intended as a general natural-language SQL model.
