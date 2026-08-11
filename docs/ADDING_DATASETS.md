# Adding or Changing Datasets

QueryGuard supports two different concepts:

1. **temporary user source** — upload through the UI; no code change;
2. **permanent demo/evaluation dataset** — add to the repository intentionally and document it.

## A. Temporary SQLite database

No code change is required.

1. Open **Database** mode.
2. Upload `.db`, `.sqlite`, or `.sqlite3`.
3. QueryGuard runs `PRAGMA quick_check`.
4. It discovers user tables, columns, primary keys, and declared foreign keys.
5. It builds a schema retriever.
6. Questions use that workspace database.
7. Click **Change source** to delete it and create another workspace.

### What if the database has no foreign keys?

QueryGuard can still retrieve/query tables, but it will not claim undeclared relationships. A future feature could let users define relationships explicitly. Automatic relationship inference is intentionally out of V1 because false relationships can produce plausible but wrong SQL.

### What about a `.sql` dump?

The final V1 uploads **SQLite database files**, not arbitrary `.sql` dumps. A SQL dump can contain dialect-specific DDL, writes, triggers, extensions, or administrative statements, so executing an untrusted dump automatically would weaken the upload-security boundary.

If you own a trusted SQLite-compatible dump, convert it to a `.sqlite` database outside the public upload endpoint, validate the resulting database, and then upload that database file. A future trusted-admin import tool could support controlled dump conversion separately from user querying.

## B. Temporary Excel workbook

1. Open **Spreadsheet** mode.
2. Upload `.xlsx`.
3. The Office ZIP container is checked for unexpected expansion.
4. Each non-empty sheet becomes a SQLite table.
5. Sheet/column labels are sanitized into SQLite-safe names.
6. Cell values are written without intentional imputation.
7. Normal schema retrieval/Text-to-SQL begins.

### Multi-sheet warning

Excel does not usually contain relational foreign-key metadata. If two sheets are logically related, the LLM may infer joins from column names, but QueryGuard does not present those as declared relationships. For important analytics, create a real SQLite database with explicit keys or add a future relationship-definition UI.

## C. Temporary CSV

CSV becomes one SQLite table named from the file. The rest of the pipeline is identical to Excel.

## D. Add a permanent SQLite demo

If replacing Chinook as the default demo:

1. Verify redistribution rights/license.
2. Add database/source under `data/<dataset>/`.
3. Add license/provenance documentation.
4. Change `QUERYGUARD_DATABASE_PATH` default only if the project truly wants a new default.
5. Create a setup script that reproduces the DB from trusted source data.
6. Add smoke checks (table counts or known aggregate values).
7. Create a new evaluation JSONL with questions, gold SQL, required tables, category, and order sensitivity.
8. Run retrieval evaluation.
9. Run Text-to-SQL evaluation with a frozen provider/model/prompt configuration.
10. Update README/results/docs.

Do not silently reuse Chinook metrics for a different database.

## E. Add a new document format

A parser must output `DocumentUnit` objects:

```python
DocumentUnit(
    source_name="file.ext",
    locator="page/section/slide",
    text="extracted text",
)
```

Implementation steps:

1. add extension to an allowlist;
2. validate file/container size;
3. implement parser under `ingestion/`;
4. preserve a human-readable locator;
5. route it in `ingestion/document_loader.py`;
6. add parsing tests;
7. add retrieval/evidence tests;
8. document limitations.

## F. Add another invoice format

Invoice mode accepts either structured rows or text/OCR.

For a new format:

1. extract text or rows;
2. map into `InvoiceRecord`;
3. set uncertain/missing fields to `None`, not invented values;
4. set `needs_review` when core fields are missing;
5. retain original source name;
6. add test fixtures;
7. evaluate field accuracy on a labeled set before claiming quality.

## G. Adding PostgreSQL later

Do not upload a PostgreSQL server dump and assume SQLite compatibility.

A production adapter would need:

- connection URL validation;
- read-only database role;
- PostgreSQL schema introspection;
- dialect-specific SQLGlot parsing/generation;
- statement timeout;
- connection pooling;
- credential/secret handling;
- integration tests.

The service interface can remain similar, but database execution should be implemented as an adapter rather than converting everything to SQLite.

## Dataset documentation checklist

Every permanent dataset should document:

- name/version;
- official source URL;
- license;
- date acquired;
- format;
- approximate size;
- key tables/fields;
- missing/duplicate concerns;
- privacy concerns;
- bias/representativeness limits;
- checksum or reproducible generation method;
- evaluation role;
- leakage controls.
