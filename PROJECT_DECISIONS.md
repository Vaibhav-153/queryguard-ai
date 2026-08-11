# Project Decision and Experiment Log

This file records why the project looks the way it does. It is intentionally kept in the repository so design choices can be explained in interviews instead of appearing as unexplained implementation details.

## Architecture decisions

| ID | Date | Decision | Problem / evidence | Trade-off / next action |
|---|---|---|---|---|
| D001 | 2026-08-10 | Use a modular monolith, not microservices or agents | One graduate developer must be able to run, test, and explain the system | Split services only when an actual scaling boundary appears |
| D002 | 2026-08-10 | Keep Chinook as the built-in demo | It is small, relational, reproducible, and supports joins/aggregations | It is not representative of enterprise data |
| D003 | 2026-08-10 | Establish an explainable lexical schema-retrieval baseline | Full-schema prompting is harder to scale and evaluate | Keep semantic retrieval optional until it shows measured value |
| D004 | 2026-08-10 | Treat prompt instructions as insufficient SQL security | A model can ignore text instructions | Parse SQL with SQLGlot and execute through a separate read-only SQLite boundary |
| D005 | 2026-08-10 | Allow at most one SQL repair attempt | Unbounded self-correction creates nondeterministic loops and cost | Security-policy failures are never repaired automatically |
| D006 | 2026-08-10 | Use exact NumPy cosine search instead of a vector database for small schemas | The index is tiny and does not justify a service/database | Revisit FAISS only for substantially larger indexes |
| D007 | 2026-08-10 | Support local Ollama and hosted providers behind one small interface | The project should not depend on a single model vendor | Keep provider-specific code small and explicit |
| D008 | 2026-08-10 | Protect hosted query endpoints with an optional shared UI/API key | A public backend could consume model quota directly | This is a preview control, not enterprise authentication |
| D009 | 2026-08-11 | Keep Chinook unchanged and add temporary upload workspaces | Users should be able to switch data sources without changing source code | Workspaces are ephemeral, filesystem-backed, and intentionally personal-project scale |
| D010 | 2026-08-11 | Convert Excel/CSV into temporary SQLite | Reusing the governed SQL pipeline is simpler than building a second analytics engine | Uploaded spreadsheets do not automatically provide relational foreign keys |
| D011 | 2026-08-11 | Use RAG for PDF/DOCX/PPTX instead of forcing documents into SQL | Unstructured text needs evidence retrieval, not relational query generation | Citation quality depends on parsing/retrieval quality |
| D012 | 2026-08-11 | Model invoice analysis as a hybrid workflow | Invoice fields support analytics while raw text supports document-specific questions | Extraction is conservative and uncertain records are flagged for review |
| D013 | 2026-08-11 | Keep OCR optional locally but include it in the API Docker image | Normal documents do not need OCR; scanned files do | Hosted free services may omit OCR system packages to stay lightweight |
| D014 | 2026-08-11 | Normalize Chinook SQL line endings before checksum validation | Git can convert CRLF/LF and change raw-byte hashes without changing SQL content | Continue failing closed if normalized content changes |
| D015 | 2026-08-11 | Add upload count, per-file size, combined-size, and Office expansion limits | Uploaded files create memory/disk/decompression risk | Limits remain configurable for different deployments |
| D016 | 2026-08-11 | Keep document retrieval lexical by default and semantic optional | Lexical mode is lightweight and explainable | Compare semantic retrieval before making superiority claims |
| D017 | 2026-08-11 | Exclude arbitrary PDF/Office editing from the core scope | Editing every document layout would turn the project into a document editor | Export analysis/results instead; simple editing can be future work |

## Measured experiments

| ID | Date | Experiment | Configuration | Result | Interpretation |
|---|---|---|---|---|---|
| E001 | 2026-08-11 | Chinook schema retrieval | lexical BM25-style, 15 hand-reviewed questions | Recall@1 0.800; Recall@3 0.967; Recall@5 0.967 | Strong small-schema baseline; one or more questions still miss at low K |
| E002 | 2026-08-11 | Synthetic document retrieval | lexical retrieval, 8 hand-authored examples | Hit@1 0.875; Hit@3 0.875 | One evidence question still misses; negative result is retained instead of hidden |
| E003 | 2026-08-11 | Synthetic invoice field extraction | heuristic parser, 3 simple hand-authored examples, 6 fields | exact field match 1.000 (18/18 field comparisons) | Smoke/evaluation set is intentionally small and is not production invoice accuracy |
| E004 | 2026-08-11 | Final artifact-runtime verification | Python 3.13.5 artifact environment | 43 passed, 13 SQLGlot-dependent skips; 68% coverage; compile/database/API/sample-ingestion/wheel smokes passed | SQLGlot, Ruff, Streamlit visual, Docker, and live model checks still require a dependency-complete target environment |

## Experiment template for real model runs

```text
Experiment ID:
Date:
Hypothesis:
Provider/model:
Prompt/version:
Retrieval strategy:
Top K:
Dataset/split:
Hardware/runtime:
Metrics:
Result:
Failure categories:
Interpretation:
Decision:
Next action:
```

Do not replace negative results with only successful examples. If a prompt/model is changed after inspecting an evaluation set, record that fact and create a fresh held-out set before calling later numbers final-test results.
