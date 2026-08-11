# UI Guide

QueryGuard's Streamlit interface is designed so a first-time reviewer can understand what each mode does without reading the source first.

## Sidebar

The sidebar shows:

- backend connection status;
- active LLM provider and model;
- retrieval strategy;
- whether the shared hosted API key is enabled;
- the purpose of Demo, Ollama, Gemini, and Groq;
- the SQL safety model.

Provider/model changes are configuration changes. They are made through `.env` locally or deployment secrets online and take effect when the API restarts. API keys are not intended to be typed into the public UI.

## Try Demo

Uses the bundled Chinook SQLite database. This is the reproducible portfolio path and requires no upload.

A question passes through schema retrieval, LLM/deterministic generation, SQL validation, read-only execution, and result presentation.

The result panel exposes:

- generated SQL;
- governance status;
- tables referenced;
- whether the single repair attempt was used;
- database-backed result rows;
- a simple chart when the result shape is suitable;
- retrieved schema context;
- request timing;
- CSV/XLSX/SQL downloads.

## Database

Accepts one `.db`, `.sqlite`, or `.sqlite3` file.

After upload the UI shows detected table, column, and relationship counts. `View detected schema` displays actual database metadata. `Change source` deletes the temporary workspace and lets the user upload another database.

The database is queried through the same governed Text-to-SQL pipeline as Chinook. It is not copied into the permanent demo database.

## Spreadsheet

Accepts one `.xlsx` or `.csv` file.

QueryGuard converts worksheet/table data to temporary SQLite, then reuses the database pipeline. This avoids maintaining a separate natural-language pandas execution engine.

Important limitation: Excel/CSV files usually do not contain declared foreign-key relationships, so QueryGuard does not invent them automatically.

## Documents

Accepts one or more `.pdf`, `.docx`, and `.pptx` files.

The UI shows an evidence-grounded answer rather than generated SQL. Under the answer, evidence expanders expose the source filename, page/section/slide locator, retrieval score, and retrieved text.

Downloads include Markdown and DOCX analysis reports containing the answer and cited evidence.

Scanned PDFs can use optional local OCR when Tesseract and the OCR extra are installed.

## Invoices

Accepts one or more invoice `.pdf`, `.png`, `.jpg`, `.jpeg`, `.xlsx`, or `.csv` files.

The workspace has two capabilities:

1. **Structured analytics** — extracted invoice fields are normalized into temporary SQLite and queried with governed Text-to-SQL.
2. **Document lookup** — when original invoice text is available, wording questions use evidence retrieval.

The UI exposes extracted records, review flags, CSV/XLSX downloads, structured analytics, and evidence-backed invoice-document answers.

Invoice extraction is intentionally conservative. A `needs_review` record should be reviewed rather than treated as accounting truth.

## Downloads

QueryGuard generates downloads in memory rather than exposing permanent public files.

Structured results can be exported as:

- SQL;
- CSV;
- XLSX.

Document analysis can be exported as:

- Markdown;
- DOCX.

Invoice records can be exported as:

- CSV;
- XLSX.

CSV/XLSX export escapes formula-like text to reduce spreadsheet formula-injection risk.

## What the UI deliberately does not do

The final V1 does not provide:

- arbitrary PDF layout editing;
- autonomous agents;
- user account/RBAC administration;
- writable production database connections;
- arbitrary Python execution.

Those exclusions keep the portfolio focused on governed analytics and evidence-grounded document reasoning.
