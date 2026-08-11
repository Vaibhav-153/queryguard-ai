# Project Manifest

**Project:** QueryGuard AI — Governed Data & Document Intelligence Platform  
**Version:** 2.0.0  
**Final artifact date:** 2026-08-11

This manifest describes the packaged GitHub-ready V2 repository. Generated caches, virtual environments, secrets, temporary workspaces, downloaded Spider data, package build directories, and `.egg-info` files are intentionally excluded.

## Packaged scope

### Built-in demo

- Chinook 1.4.5 SQLite.
- Governed natural-language → SQL → read-only execution workflow.

### User-provided structured data

- SQLite: `.db`, `.sqlite`, `.sqlite3`.
- Spreadsheet: `.csv`, `.xlsx`.
- Spreadsheets are converted into temporary SQLite and reuse the governed SQL pipeline.

### User-provided documents

- PDF `.pdf`.
- Word `.docx`.
- PowerPoint `.pptx`.
- Page/section/slide-aware extraction, chunking, retrieval, grounded answer generation, and evidence display.

### Invoice intelligence

- PDF, PNG, JPG/JPEG, XLSX, CSV.
- Conservative field extraction with `needs_review` flags.
- Normalized invoice SQLite analytics.
- Raw invoice evidence retained when text is available.
- OCR is optional locally and requires Tesseract + `pytesseract`.

### LLM providers

- `demo` — deterministic tests/smokes.
- `ollama` — local/offline provider.
- `gemini` — recommended hosted provider configuration.
- `groq` — optional hosted alternative.

### Application and operations

- FastAPI backend.
- Streamlit UI.
- Docker API/UI images and Compose file.
- Render backend Blueprint.
- Streamlit Community Cloud configuration.
- GitHub Actions test workflow.

## Repository counts

The final cleaned repository contains **168 files**:

| Area | Files |
|---|---:|
| Repository root | 17 |
| `.github/` | 1 |
| `.streamlit/` | 2 |
| `app/` | 3 |
| `assets/` | 1 |
| `data/` | 11 |
| `docs/` | 28 |
| `examples/` | 6 |
| `reports/` | 1 |
| `results/` | 6 |
| `scripts/` | 7 |
| `src/` | 65 |
| `tests/` | 20 |

Additional code/documentation counts:

- Python files across app/source/tests/scripts: **95**.
- QueryGuard source package Python files: **65**.
- Test modules: **19**.
- Documentation Markdown files under `docs/`: **28**.

These counts describe the packaged artifact, not generated files created after installation/testing.

## Important entry points

| File | Purpose |
|---|---|
| `README.md` | Recruiter-facing overview and quick start |
| `app/streamlit_app.py` | Multi-mode user interface |
| `app/api_client.py` | Streamlit → FastAPI HTTP client |
| `src/queryguard/api/main.py` | FastAPI application and endpoint wiring |
| `src/queryguard/services/query_service.py` | Governed Text-to-SQL orchestration |
| `src/queryguard/services/document_service.py` | Evidence-oriented document Q&A |
| `src/queryguard/workspaces/manager.py` | Temporary source isolation/switching |
| `src/queryguard/governance/validator.py` | SQLGlot AST safety policy |
| `src/queryguard/database/connection.py` | Read-only SQLite execution boundary |
| `src/queryguard/llm/factory.py` | Demo/Ollama/Gemini/Groq provider selection |
| `scripts/setup_chinook.py` | Reproducible demo DB build |
| `scripts/verify_project.py` / `queryguard-verify` | Chinook/application smoke verification |
| `.github/workflows/tests.yml` | Hosted lint/compile/data/test gate |

For complete file-to-file interconnections, see `docs/CODEBASE_GUIDE.md`.

## Verification snapshot

Artifact-runtime verification on Python 3.13.5:

- Python compilation: **Passed**.
- Package wheel build without dependency resolution: **Passed**.
- Chinook rebuild/integrity smoke: **Passed**.
- FastAPI `/health` smoke: **Passed**.
- Sample CSV/PDF/DOCX/PPTX/invoice ingestion smokes: **Passed**.
- OCR integration smoke: **Passed pipeline invocation; accuracy not measured**.
- Tests: **43 passed, 13 skipped**.
- Skips: **all SQLGlot-dependent**, because SQLGlot was not installed in the artifact runtime.
- Artifact-runtime coverage: **68%**.
- Secret-pattern repository scan: **No selected live-key patterns found**.

Measured component results:

- Chinook schema lexical Recall@1: **0.800**.
- Chinook schema lexical Recall@3: **0.967**.
- Chinook schema lexical Recall@5: **0.967**.
- Synthetic document lexical Hit@1/Hit@3: **0.875 / 0.875**.
- Synthetic invoice field exact match: **1.000** on 3 simple hand-authored text examples (not production accuracy).

Not verified in the artifact runtime:

- SQLGlot-dependent governed SQL acceptance suite;
- Ruff execution;
- live Ollama/Gemini/Groq inference;
- Streamlit visual/browser rendering;
- semantic Sentence Transformer retrieval;
- Docker build/run;
- V2 live Render/Streamlit deployment;
- V2 GitHub Actions hosted execution.

See `reports/BUILD_VERIFICATION.md` for the authoritative tested/not-tested boundary.

## Dataset integrity references

Chinook normalized SQL SHA-256:

```text
caf31d698a4a79c628215b552dfe6575e71be052ae02b8f18e763498f55f5d44
```

Generated SQLite SHA-256:

```text
79df86ebd5c45f009ed35dbb19757cac4f9afb393352e3d2ffe128a60a2ea718
```

Verified smoke values:

- Customers: 59.
- Tracks: 3,503.
- Invoice revenue: 2328.60.

## Documentation map

The detailed learning/interview material is under `docs/`. Recommended reading order:

1. `PROJECT_REPORT.md`
2. `BUILD_FROM_SCRATCH.md`
3. `ARCHITECTURE.md`
4. `CODEBASE_GUIDE.md`
5. `FEATURES.md`
6. `THEORY_GUIDE.md`
7. `UI_GUIDE.md`
8. `API_REFERENCE.md`
9. `LOCAL_SETUP.md`
10. `LLM_GUIDE.md`
11. `ADDING_DATASETS.md`
12. `TESTING.md`
13. `EVALUATION.md`
14. `SECURITY.md`
15. `INTERVIEW_GUIDE.md`
16. `HIRING_PACKAGE.md`
17. `FINAL_REVIEW.md`

## Final release rule

Do not call the repository fully green until a normal dependency-complete GitHub/Codespaces/local run successfully executes:

```bash
pip install -e ".[ui,dev]"
ruff check app src tests scripts
python -m compileall -q src app tests scripts
python scripts/setup_chinook.py
queryguard-verify
pytest -v
```

In particular, the SQLGlot-dependent tests must run rather than skip before the full governed SQL path is declared release-verified.
