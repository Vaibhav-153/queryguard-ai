# Project Report

## 1. Problem

Many business questions are stored in structured databases/spreadsheets or buried inside documents. A user may know the question they want to ask but not know SQL, the database schema, the location inside a long report, or how to combine many invoices safely.

A naive LLM solution has several risks:

- hallucinated table/column names;
- destructive SQL;
- plausible but wrong aggregation;
- sending entire schemas/documents unnecessarily;
- answers with no evidence;
- mixing files from different users/sessions;
- silently guessing missing invoice values.

QueryGuard AI addresses these as an engineering pipeline rather than a single model call.

## 2. Intended users

- junior/data analysts exploring unfamiliar SQLite data;
- small teams with Excel/CSV analytical data;
- students/recruiters testing a governed GenAI workflow;
- users searching non-sensitive PDF/DOCX/PPTX files;
- personal invoice analysis where manual review is acceptable.

## 3. Inputs and outputs

### Structured

Input: natural-language question + active SQLite-compatible workspace.

Output: generated SQL, governance result, retrieved schema evidence, database rows, simple chart recommendation, deterministic explanation, latency, downloadable result.

### Documents

Input: natural-language question + uploaded document chunks.

Output: grounded LLM answer + source evidence containing filename and page/section/slide locator.

### Invoices

Input: invoice documents/images/spreadsheets.

Output: normalized fields with `needs_review`, analytics database, document evidence where available, exports.

## 4. Scope

### Core

- bundled Chinook demo;
- SQLite upload;
- Excel/CSV conversion;
- governed Text-to-SQL;
- document parsing/retrieval;
- invoice normalization;
- downloads;
- Demo/Ollama/Gemini/Groq;
- FastAPI/Streamlit;
- tests, Docker, CI, documentation.

### Advanced differentiators

1. AST SQL governance + independent read-only execution.
2. Dynamic schema/document retrieval with measurable retrieval metrics.
3. Hybrid invoice pipeline combining structured analytics and document evidence.

### Stretch/production evolution

- PostgreSQL/MySQL adapters;
- durable authenticated workspaces;
- row/column permissions;
- learned invoice extraction;
- rerankers;
- background ingestion;
- enterprise observability.

### Explicitly out of scope

- autonomous agents;
- writable arbitrary databases;
- Kafka/Kubernetes only for keywords;
- arbitrary PDF layout editing;
- safety-critical financial decision automation.

## 5. Baseline and advanced path

The original reproducible baseline is the Chinook flow:

```text
question → full application schema/retrieval → demo/LLM SQL → safe execution
```

Measured schema retrieval provides an independent component result. The final repository adds user workspaces and document/invoice paths without deleting the original baseline.

## 6. Technology choices

| Need | Choice | Reason | Main limitation |
|---|---|---|---|
| Backend API | FastAPI | typed request/response, simple testing | not a full auth platform |
| Demo DB | SQLite/Chinook | reproducible, serverless, relational | limited concurrent write use; QueryGuard is read-only anyway |
| SQL AST | SQLGlot | structural policy instead of regex | dialect/version awareness |
| Dataframes | pandas | straightforward CSV/Excel conversion | memory-bound for large data |
| XLSX | openpyxl | mature Python XLSX support | macro formats deliberately rejected |
| PDF | PyMuPDF | page-aware extraction | scanned pages need OCR |
| DOCX | python-docx | paragraph/table access | complex layout not preserved as semantic structure |
| PPTX | python-pptx | slide/text/table access | charts/images not deeply interpreted |
| OCR | Tesseract optional | local/open-source | installation + scan-quality dependence |
| UI | Streamlit | fast Python portfolio UI | less frontend control than React |
| Local LLM | Ollama | local HTTP inference | hardware-dependent |
| Hosted LLM | Gemini | simple hosted demo option | provider terms/quotas change |
| Alternative hosted | Groq | model choice/faster hosted alternative | provider/model availability changes |

## 7. Security model

The security story uses multiple independent controls:

```text
Prompt rules
   ↓
SQL AST validation
   ↓
Active-schema table allowlist
   ↓
SQLite read-only URI
   ↓
PRAGMA query_only
   ↓
Timeout + row limit
```

Uploads add filename sanitization, extension/size allowlists, Office ZIP limits, workspace isolation, and expiry.

## 8. Data strategy

Chinook is the public reproducible demo. User uploads are temporary. The repository includes small hand-authored evaluation sets but does not claim they represent production distributions.

Spider remains optional because it is a separate benchmark with separate licensing and size.

## 9. Evaluation

### Measured in the final artifact environment

- Chinook lexical schema retrieval: Recall@1 0.800, Recall@3 0.967, Recall@5 0.967.
- Synthetic document retrieval: Hit@1/3 0.875 on 8 questions.
- Synthetic invoice extraction: 1.000 field exact match over 18 simple expected fields across 3 hand-authored examples.
- Demo database integrity: 59 customers, 3,503 tracks, invoice revenue 2328.60.

### Not automatically claimed

- real Gemini execution accuracy;
- real Ollama execution accuracy;
- semantic-retrieval improvement;
- OCR accuracy;
- real-world invoice extraction accuracy;
- business cost/time savings.

These require target-machine/provider/data evaluation.

## 10. Known failures/limitations

The synthetic document lexical benchmark intentionally exposes a miss: the question “minimum password length” does not share enough lexical tokens with a chunk that says “Passwords must contain at least 12 characters”. A semantic retriever or synonym expansion should improve this case. This negative result is kept instead of modifying the test only to produce 100%.

Spreadsheet workbooks generally do not declare foreign keys. QueryGuard therefore does not invent relationships. Multi-table Excel questions may require descriptive names or future user-defined relationships.

Invoice extraction uses transparent heuristics and manual-review flags. It is not a replacement for production document AI.

## 11. Production evolution

A production version would separate compute and durable workspace storage, authenticate users, encrypt data at rest, add object storage/database metadata, row/column authorization, audit events, retention controls, background ingestion, provider policy controls, and evaluated domain-specific extraction.

These are not implemented in V1 because the personal project should remain understandable and locally reproducible.

## 12. Learning outcomes

The project demonstrates that an LLM application is more than prompting. The important engineering is around retrieval, validation, deterministic boundaries, data modeling, failure handling, evaluation, API contracts, configuration, testing, deployment, and honest limitations.
