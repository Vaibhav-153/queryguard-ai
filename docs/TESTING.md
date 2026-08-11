# Testing Guide

Software tests protect behavior; AI evaluation measures quality. QueryGuard keeps those concepts separate.

## Run all deterministic checks

```bash
ruff check app src tests scripts
python -m compileall -q src app tests scripts
python scripts/setup_chinook.py
queryguard-verify
pytest -v
```

## Unit tests

### Ambiguity tests

Protect deterministic clarification rules.

Failure means a known vague question is being handled differently.

### Retrieval tests

Protect schema/document ranking behavior on simple examples.

Failure means tokenization/ranking changes need investigation.

### LLM HTTP mock tests

No real provider key/network is used. Mock responses verify:

- API key/header placement;
- response extraction;
- SQL adapter cleanup;
- missing-key configuration errors.

Failure means provider integration code changed, not that the real provider is offline.

### Spreadsheet loader tests

Create a temporary CSV and verify actual SQLite row count after conversion.

### Export tests

Verify CSV/XLSX result exports preserve normal values and escape formula-like strings before a spreadsheet application can interpret them as formulas.

### DOCX/PPTX/PDF loader tests

Generate temporary files using their real Python libraries and verify source locators/text.

### Invoice parser tests

Protect transparent field extraction on a known example.

## Integration tests

### Database integration

Uses real bundled Chinook SQLite to verify schema and read-only execution.

### Workspace integration

Builds temporary custom SQLite/XLSX sources and verifies dynamic metadata.

### QueryService integration

Uses the deterministic demo SQL generator plus real SQLGlot and SQLite.

## Security tests

Curated statements include:

```text
DELETE
UPDATE
DROP
CREATE
PRAGMA
ATTACH
multiple statements
unapproved tables
```

A safe join and CTE are also tested so the policy does not simply reject everything.

## API tests

Protect:

- `/health`;
- demo query contract;
- shared-key rejection;
- multipart document upload/workspace creation;
- upload-count enforcement;
- document-query workspace flow.

## OCR testing

OCR is optional and requires a system binary. Core CI does not require it. A production OCR pipeline should have its own image/scan quality benchmark rather than a single smoke test.

## What a failed test means

Do not automatically change expected values until tests pass. First decide whether:

1. implementation is wrong;
2. requirement intentionally changed;
3. fixture/evaluation data is wrong;
4. dependency behavior changed.

Document meaningful behavior changes in `PROJECT_DECISIONS.md`.
