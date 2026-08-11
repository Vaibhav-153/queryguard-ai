# Final Build Verification

**Date:** 2026-08-11  
**Version:** QueryGuard AI 2.0.0  
**Status:** Partially verified — deterministic components were executed; dependency- or service-specific checks that could not run are listed explicitly.

This report is the authoritative build-status document for the packaged V2 repository. Older verification counts from the original project were replaced rather than carried forward.

## What V2 contains

The final repository keeps the original Chinook governed Text-to-SQL demo and adds:

- temporary SQLite database upload/switching;
- CSV/XLSX → SQLite analytics;
- PDF/DOCX/PPTX parsing and evidence-oriented document Q&A;
- invoice PDF/image/XLSX/CSV ingestion with normalized analytics and raw-text evidence where available;
- workspace isolation and upload resource limits;
- CSV/XLSX/SQL/Markdown/DOCX downloads;
- Demo, Ollama, Gemini, and Groq provider support behind one small provider interface;
- FastAPI upload/query endpoints and a multi-mode Streamlit interface;
- expanded unit, integration, API, security, ingestion, retrieval, export, and example tests;
- complete local/deployment/theory/codebase/interview documentation.

## Build environment

- Artifact runtime Python: **3.13.5**.
- Repository target: **Python >=3.11**.
- Default deterministic provider: `demo`.
- Built-in data source: Chinook 1.4.5 SQLite.
- Artifact runtime did **not** contain SQLGlot, Streamlit, Sentence Transformers, or Docker.
- Tesseract + `pytesseract` were available for an OCR pipeline smoke check.

## Source compilation — Passed

Executed:

```bash
python -m compileall -q src app tests scripts
```

Result: no syntax errors.

## Packaging — Passed

Executed without dependency resolution:

```bash
python -m pip wheel . --no-deps --no-build-isolation
```

Result:

- wheel: `queryguard_ai-2.0.0-py3-none-any.whl`
- SHA-256: `85973bd898d4ea53b9ef7a333ca21a20da3854c2bf58a3b3559f340ab89e79df`

This verifies Python package metadata/build structure. It is not a substitute for installing every declared dependency on the target machine.

## Chinook rebuild and database smoke verification — Passed

Executed:

```bash
python scripts/setup_chinook.py
queryguard-verify
```

Measured results:

- SQLite integrity: `ok`
- user tables: 11
- customers: **59**
- tracks: **3,503**
- total invoice revenue smoke check: **2328.60**
- normalized SQL SHA-256: `caf31d698a4a79c628215b552dfe6575e71be052ae02b8f18e763498f55f5d44`
- generated SQLite SHA-256: `79df86ebd5c45f009ed35dbb19757cac4f9afb393352e3d2ffe128a60a2ea718`

The setup script now hashes LF-normalized SQL content, avoiding false failures caused only by CRLF/LF Git line-ending conversion while still failing if the canonical content changes.

## Automated tests — Partially executed

Executed:

```bash
pytest -ra
```

Result:

- **43 passed**
- **13 skipped**

Every skip is an SQLGlot-dependent governance or governed SQL end-to-end test. SQLGlot is a required dependency in `pyproject.toml`, but it is not installed in this artifact runtime and public package download was unavailable here.

Skipped areas:

- one FastAPI governed query test;
- two QueryService governed SQL integration tests;
- SQLGlot AST governance/security tests, including destructive operations, multiple statements, unknown tables, safe joins, and CTE behavior.

The final GitHub workflow installs `.[ui,dev]` before running the suite, so the **release acceptance gate is a GitHub/Codespaces run with zero dependency-related skips**. This artifact does not claim that gate has already passed.

## Coverage — Measured in artifact runtime

Executed:

```bash
pytest --cov=queryguard --cov-report=term -q
```

Overall line coverage: **68%**.

Interpretation:

- ingestion, workspace, document retrieval, exports, and many provider/configuration paths are covered;
- SQLGlot-dependent `QueryService`/governance execution paths are under-covered in this environment because those tests were skipped;
- semantic model loading, live provider calls, and some presentation paths are intentionally not exercised here.

This is a measured artifact-runtime coverage number, not a production quality guarantee.

## Sample file ingestion smokes — Passed

The synthetic examples bundled in `examples/` were parsed using the final code:

- `sample_sales.csv` → one temporary SQLite table with **5 rows**;
- `sample_policy.pdf` → **2** page units;
- `sample_handbook.docx` → **3** section/paragraph units;
- `sample_briefing.pptx` → **2** slide units;
- `sample_invoices.csv` → **3** normalized invoice records; first sample total `132.0`.

These are smoke inputs, not hidden benchmark data.

## OCR pipeline smoke — Passed; accuracy not measured

Tesseract/pytesseract were available in the artifact runtime. A generated invoice image was passed through the OCR helper and text was returned, including the invoice number and amount text.

This verifies that the OCR integration can invoke Tesseract. It **does not** establish OCR accuracy on real invoices. The product retains manual-review flags and documents OCR as optional for local installation.

## FastAPI health smoke — Passed

A local Uvicorn server was started from the final application and `GET /health` returned HTTP success with:

- version `2.0.0`;
- Chinook database available;
- provider `demo` / model `deterministic-demo`;
- lexical retrieval;
- upload/resource limits;
- supported source types.

A real governed SQL `/query` run was not executed in this artifact runtime because it requires SQLGlot.

## Configuration syntax — Passed

Parsed successfully:

- `pyproject.toml`;
- `.streamlit/config.toml`;
- `render.yaml`;
- `docker-compose.yml`.

This validates syntax/structure only; it does not prove a Docker/Render/Streamlit deployment.

## Repository-level secret scan — Passed for selected key patterns

A final text-file scan found no obvious committed values matching common Gemini legacy, Groq, GitHub, or `sk-...` API-key patterns.

The final repository contains only secret **names/placeholders** in `.env.example`, Streamlit examples, and deployment configuration. This check is useful but not equivalent to an enterprise secret scanner.

## Measured retrieval/extraction evaluations

### Chinook schema retrieval

15 hand-reviewed evaluation questions:

- Recall@1: **0.800**
- Recall@3: **0.967**
- Recall@5: **0.967**

Artifact: `results/lexical_retrieval_baseline.json`.

### Synthetic document retrieval

8 small hand-authored examples:

- Hit@1: **0.875**
- Hit@3: **0.875**

Artifact: `results/document_retrieval_synthetic.json`.

The retained miss is intentional negative evidence; it is not hidden from the report.

### Synthetic invoice field extraction

3 small hand-authored text examples, 6 fields:

- exact field match: **1.000**

Artifact: `results/invoice_extraction_synthetic.json`.

This is a parser smoke/evaluation fixture and **must not be described as production invoice or OCR accuracy**.

## Explicitly not verified in the artifact runtime

The following remain `Not tested` rather than being represented as successful:

- SQLGlot-dependent governed SQL tests/end-to-end SQL execution;
- Ruff lint execution (Ruff binary unavailable here; CI is configured to run it);
- Streamlit visual/browser rendering;
- Sentence Transformer semantic retrieval/model download;
- live Gemini API inference;
- live Groq API inference (HTTP behavior is covered by mocks only);
- live Ollama/model inference;
- real Text-to-SQL execution-match accuracy for Gemini/Groq/Ollama;
- real document answer-quality/citation-quality benchmark;
- real invoice/OCR dataset accuracy;
- Docker build/run;
- live Render V2 deployment;
- live Streamlit Community Cloud V2 deployment;
- V2 GitHub Actions hosted execution;
- concurrency/load testing on hosted infrastructure.

## Release acceptance on GitHub / a normal machine

Before describing the repository as fully green, run:

```bash
python -m pip install --upgrade pip
pip install -e ".[ui,dev]"
ruff check app src tests scripts
python -m compileall -q src app tests scripts
python scripts/setup_chinook.py
queryguard-verify
pytest -v
```

Expected release gate:

1. Ruff passes.
2. Chinook verification passes.
3. SQLGlot imports normally.
4. **No SQLGlot-dependent test is skipped.**
5. Full pytest suite is green.

Then separately test the desired LLM provider, Streamlit UI, Docker, and hosted deployment before publishing provider-specific accuracy or deployment claims.

## Honest conclusion

V2 is **implementation-complete and substantially verified at the deterministic/component level** in this artifact environment. The remaining acceptance work is dependency/service-specific rather than hidden: SQLGlot/full governed SQL, Ruff, Streamlit visual rendering, Docker, live LLM inference, and hosted V2 deployment must be run in a normal networked development/deployment environment.
