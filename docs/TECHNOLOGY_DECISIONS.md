# Technology Decisions

Every dependency in QueryGuard is tied to an implemented requirement. The project deliberately avoids infrastructure that would exist only as a resume keyword.

| Technology | Where it is used | Requirement | Why this choice | Main limitation / replacement condition |
|---|---|---|---|---|
| Python 3.11+ | Entire repository | readable backend/data/AI implementation | broad ecosystem and approachable code | use another language only for a proven production requirement |
| FastAPI | `src/queryguard/api/` | typed HTTP API, uploads, OpenAPI | Pydantic integration and simple testing | frontend-only apps could avoid a separate API |
| Streamlit | `app/` | recruiter-facing interactive UI | fast Python-only demonstration | replace with React/other frontend if product UX becomes primary |
| SQLite | demo and temporary structured workspaces | zero-server relational analytics | portable, reproducible, supports read-only URI mode | PostgreSQL adapter for concurrency/dialect realism |
| pandas | spreadsheet/invoice ingestion and exports | read/transform tabular files | clear DataFrame workflow | very large files would need streaming/larger-data tools |
| openpyxl | `.xlsx` | Excel parsing/writing | standard Python workbook support | not used for legacy `.xls` or macro execution |
| PyMuPDF | PDF ingestion | page text extraction and PDF rendering for OCR | page-aware parsing with a simple API | complex layouts/tables may need specialist parsers |
| python-docx | DOCX ingestion/report export | paragraph/table extraction and DOCX output | simple Office document API | advanced layout fidelity is not a project goal |
| python-pptx | PPTX ingestion | slide text/table extraction | keeps slide provenance | charts/images are not semantically interpreted in V1 |
| Pillow + optional pytesseract/Tesseract | scanned invoices/PDF pages | OCR when text is image-only | common local OCR path | OCR quality varies; cloud preview may omit the system binary |
| SQLGlot | `governance/validator.py` | structural SQL policy | AST inspection is stronger than regex matching | parser/dialect behavior still needs tests and upgrades |
| Custom BM25-style retrieval | schema/document baseline | explainable Top-K retrieval | small enough to teach and measure | semantic retrieval may outperform it on paraphrases |
| Sentence Transformers (optional) | semantic retrieval | local embeddings | no mandatory embedding API | model download/RAM makes it unsuitable for every free host |
| NumPy exact cosine | semantic ranking | vector similarity for small indexes | no vector DB/service needed | FAISS/ANN when index scale makes linear search material |
| httpx | LLM adapters + Streamlit API client | HTTP provider calls | one lightweight client instead of multiple provider SDKs | provider SDK may be adopted if it gives needed auth/reliability |
| Ollama | local provider | offline/private LLM inference | simple local server and model switching | hardware-dependent latency/model size |
| Gemini adapter | hosted provider | public online demo | no local model process on the backend | quota/model availability and data-use policies must be reviewed |
| Groq adapter | optional hosted provider | alternate hosted model | reduces single-provider dependency | availability/quota can change |
| pytest | tests | repeatable unit/integration/security checks | standard Python testing | none for current scale |
| Ruff | CI quality | lint + format | fast single-tool quality gate | no reason to replace currently |
| Docker Compose | local reproducibility | API/UI containers and workspace volume | understandable two-service local deployment | Kubernetes would be overengineering here |
| GitHub Actions | CI | fresh-environment verification | repository-native automation | another CI only if hosting requirements change |
| Render + Streamlit Community Cloud | portfolio deployment | separate hosted API and UI | simple GitHub-connected preview | not presented as enterprise production infrastructure |

## Why there is no agent framework

The important flows are deterministic: retrieve schema/evidence, generate, validate, execute or answer. An autonomous agent would make retries, tool calls, security review, testing, and cost harder to reason about without solving a demonstrated problem.

## Why there is no vector database

A Chinook schema has only a small number of table documents and personal document workspaces are intentionally bounded. Exact in-memory ranking is easier to explain and deploy. A persistent vector database should be introduced only when index size, persistence, or multi-user search makes it necessary.

## Why Excel/CSV become SQLite

This is deliberate reuse. After a spreadsheet becomes a temporary relational database, the same schema extraction, retrieval, SQL validation, read-only execution, metrics, and exports can be used. Maintaining one governed analytics engine is easier to test than creating independent DataFrame-question logic.

## Why document files use RAG instead of SQL

PDF/DOCX/PPTX text is unstructured. QueryGuard preserves page/section/slide locators, retrieves relevant chunks, and supplies only that evidence to the LLM. This makes sources inspectable and prevents pretending document text is a relational schema.
