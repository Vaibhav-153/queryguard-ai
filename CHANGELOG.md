# Changelog

## 2.0.0 — 2026-08-11

Final portfolio release candidate.

### Added

- temporary user workspaces with source switching;
- SQLite database upload and dynamic schema extraction;
- Excel/CSV to temporary SQLite analytics;
- PDF/DOCX/PPTX source-aware ingestion and RAG;
- invoice PDF/image/XLSX/CSV normalization and hybrid analytics;
- CSV/XLSX/SQL/Markdown/DOCX downloads;
- generic Demo/Ollama/Gemini/Groq text-LLM layer;
- upload count, combined-size, and Office expansion limits;
- optional OCR and OCR-enabled API Docker image;
- document and invoice component evaluations;
- expanded tests, CI, deployment configuration, theory, codebase, dataset, and interview documentation.

### Changed

- Chinook remains the permanent built-in demo rather than the only supported data source;
- SQL generation now wraps the generic LLM layer instead of duplicating provider clients;
- Chinook SQL checksum validation normalizes line endings for cross-platform reproducibility;
- Render shared access key is now an explicitly supplied secret (`sync: false`);
- hosted preview workspaces use smaller temporary resource limits.

### Removed

- stale YAML configuration files that were not loaded by the application;
- cache/bytecode artifacts and conflicting historical verification records;
- unnecessary claim that every provider/LLM path was tested when no real key/model was available.
