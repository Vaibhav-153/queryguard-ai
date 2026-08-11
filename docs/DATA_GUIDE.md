# Data Guide

## Chinook demo

Purpose: stable relational demo/evaluation database.

Version used: Chinook `v1.4.5` SQLite.

Upstream project:

```text
https://github.com/lerocha/chinook-database
```

License: MIT; upstream attribution is preserved under `data/chinook/`.

Verified smoke values:

- Customers: 59
- Tracks: 3,503
- Total invoice revenue: 2328.60

### Portable SQL checksum

Git normalizes `.sql` files to LF through `.gitattributes`. `scripts/setup_chinook.py` therefore normalizes line endings before SHA-256 validation.

Normalized SQL SHA-256:

```text
caf31d698a4a79c628215b552dfe6575e71be052ae02b8f18e763498f55f5d44
```

Reference generated SQLite SHA-256 from the original verified build:

```text
79df86ebd5c45f009ed35dbb19757cac4f9afb393352e3d2ffe128a60a2ea718
```

The database-file byte hash can depend on generation details; source integrity + record/schema smoke checks are more important than silently changing a reference hash.

## User uploads

User uploads are not permanent project datasets. They live under `data/workspaces/`, are Git-ignored, use random workspace IDs, and expire.

Do not use a public hosted demo with confidential or regulated data.

## Spreadsheet ingestion

CSV/XLSX cell values are not intentionally imputed. QueryGuard sanitizes **labels** (table/column names) for SQLite but does not silently fill missing values.

Excel sheets become tables. No foreign-key relationship is invented unless the source database actually declares one.

## Document ingestion

PDF/DOCX/PPTX text becomes source-aware units and chunks. The original location (page/section/slide) remains attached for evidence.

## Invoice extraction

Structured fields may be missing. `needs_review` makes this visible.

The application should not interpret missing extraction as zero.

## Evaluation data

### `chinook_eval.jsonl`

15 project-specific Text-to-SQL/schema-retrieval questions with gold SQL and required tables.

### Synthetic document retrieval

Hand-authored evidence chunks + 8 questions. Purpose: transparent retrieval regression test, not production RAG benchmarking.

### Synthetic invoices

Three simple hand-authored invoice texts. Purpose: verify parser regressions. They are intentionally easier than real OCR/layout data.

## Optional Spider

Spider 1.0 is not bundled. It has separate licensing/provenance and can be downloaded with:

```bash
python -m pip install gdown
python scripts/download_spider.py
```

Before use, verify the current benchmark/license at:

```text
https://yale-lily.github.io/spider
```

Public LLMs may have encountered public benchmark material during training; report Spider results as benchmark results rather than production accuracy.

## Leakage prevention

- keep prompt development examples separate from final evaluation where possible;
- do not repeatedly tune against the same final set and still call it untouched;
- keep paraphrases/business-equivalent questions grouped;
- record provider/model/prompt/retrieval configuration with results.
