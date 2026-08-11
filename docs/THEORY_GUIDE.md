# Theory Guide

## 1. Relational databases

A relational database organizes data into tables. A **primary key** uniquely identifies a row. A **foreign key** describes a relationship between tables.

Example:

```text
Customer(CustomerId PK)
Invoice(InvoiceId PK, CustomerId FK → Customer.CustomerId)
```

A join combines related rows:

```sql
SELECT c.CustomerId, SUM(i.Total)
FROM Customer AS c
JOIN Invoice AS i ON i.CustomerId = c.CustomerId
GROUP BY c.CustomerId;
```

Why this matters in QueryGuard: the LLM must discover which tables and joins answer the user question.

## 2. Text-to-SQL

Text-to-SQL maps a natural-language question to an executable SQL query.

Major subproblems:

1. understand analytical intent;
2. link words to schema entities;
3. choose joins;
4. choose filters/aggregation/order;
5. produce correct dialect;
6. execute safely;
7. determine whether the result matches intent.

Syntactic correctness is not semantic correctness. A query can run successfully while answering the wrong question.

## 3. Schema linking and retrieval

For a large schema, sending every table can add irrelevant context. QueryGuard creates one searchable document per table containing table name, columns, and declared relationships.

A retriever ranks them against the question.

### BM25 intuition

BM25 rewards terms that:

- appear in the candidate document;
- are relatively rare across documents;
- occur enough times to be informative without increasing score forever;
- account for document length.

QueryGuard uses a small BM25-style implementation because schema sets are usually small and explainability matters.

### Recall@K

If a question requires `Customer` and `Invoice`, and top-3 retrieval returns both, Recall@3 is 1.0.

For required set `R` and retrieved top-K `K`:

```text
Recall@K = |R ∩ K| / |R|
```

## 4. Embeddings and cosine similarity

Semantic retrieval represents text as vectors. Similar meanings can have nearby vectors even when exact words differ.

With normalized vectors, cosine similarity is a dot product:

```text
similarity(q, d) = q · d
```

QueryGuard optionally uses Sentence Transformers. It does not require FAISS for small indexes; a linear NumPy search is simpler and adequate until scale requires ANN.

## 5. Abstract syntax trees

Regex is weak for SQL security because SQL can contain nesting, aliases, CTEs, comments, and dialect variations.

A parser converts SQL into an AST. QueryGuard examines structural node types and physical tables.

Example conceptually:

```text
SELECT ...
  ├── FROM Customer
  └── JOIN Invoice
```

A `Delete`, `Drop`, `Attach`, or other denied node can be rejected even when surrounded by formatting or nesting.

## 6. Defense in depth

A prompt is not a security boundary. QueryGuard uses:

1. prompt restrictions;
2. AST validation;
3. table allowlist;
4. read-only SQLite connection;
5. `PRAGMA query_only`;
6. timeout;
7. row limit.

This is **defense in depth**: multiple controls protect the same high-value action.

## 7. Query timeout

SQLite supports a progress handler. QueryGuard periodically checks a deadline and interrupts a long query.

This protects the personal demo from accidentally expensive queries. It is not a full database resource governor.

## 8. RAG

Retrieval-Augmented Generation separates finding evidence from writing an answer.

```text
Question
  ↓
Retrieve evidence
  ↓
LLM receives only relevant evidence
  ↓
Grounded answer + citations
```

Benefits:

- smaller prompts;
- inspectable evidence;
- reduced pressure to hallucinate;
- reusable retrieval evaluation.

RAG does not guarantee truth. Bad retrieval or model interpretation can still produce an incorrect answer.

## 9. Chunking

Long documents are split into chunks because models/retrievers work better on bounded pieces.

Trade-off:

- chunks too small → context is fragmented;
- chunks too large → retrieval is less precise and prompts grow.

QueryGuard keeps source locators and uses overlap so statements near boundaries are less likely to disappear.

## 10. Prompt injection in documents

A document may contain text such as “ignore previous instructions”. In a RAG system that text is untrusted source data.

QueryGuard's document system prompt explicitly tells the model to treat document text as evidence, not instructions. This reduces risk but is not a formal proof against all model-level prompt injection.

## 11. Invoice extraction

Invoices are semi-structured: common concepts exist, but layouts vary.

QueryGuard's explainable baseline uses labels/regex/column aliases and records missing/uncertain fields rather than inventing them.

A stronger production system might use a layout-aware model, vendor templates, OCR confidence, or managed document AI and would need a labeled evaluation set.

## 12. API design

FastAPI separates UI and backend:

```text
UI → HTTP request → validated Pydantic model → service → response model
```

Benefits:

- Streamlit does not need database/LLM secret logic;
- endpoints can be tested independently;
- another frontend could reuse the API.

## 13. Configuration and secrets

Configuration that changes by environment belongs in environment variables, not source code.

Examples:

```text
QUERYGUARD_LLM_PROVIDER
QUERYGUARD_OLLAMA_MODEL
QUERYGUARD_GEMINI_API_KEY
```

`SecretStr` reduces accidental display but does not replace secret-management hygiene.

## 14. Testing layers

- **unit tests:** one function/module behavior;
- **integration tests:** real SQLite/workspace components together;
- **API tests:** HTTP contract;
- **security tests:** denied/allowed SQL cases;
- **evaluation:** model/retrieval quality measurements, not just software correctness.

A passing unit test does not mean an LLM has high accuracy. Software tests and AI evaluation answer different questions.

## 15. CI/CD

GitHub Actions runs deterministic checks after each push:

```text
install → lint → compile → rebuild demo DB → smoke verify → pytest
```

It deliberately does not require paid/provider API keys.

## 16. Local vs hosted LLMs

### Local

Pros: privacy/control/no per-request cloud dependency.

Cons: hardware, setup, slower models on weak machines.

### Hosted

Pros: no local GPU, easy public demo.

Cons: keys, quotas, provider policy, data sent over network.

The provider abstraction exists because this is a requirement trade-off, not because multiple providers are a resume keyword.
## 17. Temporary workspace isolation

A file upload is not treated as a permanent project dataset. QueryGuard creates a random workspace directory, stores only sanitized basenames inside it, writes derived artifacts such as `workspace.sqlite` or chunk JSON there, and records an expiry time.

This pattern solves two problems at personal-project scale:

1. the built-in Chinook demo stays reproducible;
2. changing one user's source does not require changing application code/global database configuration.

A production multi-user system would normally replace local filesystem state with authenticated durable storage and a stronger lifecycle/retention service.

## 18. Spreadsheet-to-SQL normalization

Excel/CSV are tabular but are not automatically relational databases. QueryGuard deliberately converts them into temporary SQLite because the project already has a tested query/safety boundary for SQLite.

Benefits:

- reuse schema extraction;
- reuse Text-to-SQL prompts;
- reuse SQLGlot policy;
- reuse read-only execution;
- one result/export path.

Trade-off: spreadsheet files rarely contain declared foreign keys. Similar column names are not proof of a relationship, so V1 does not invent relationship metadata.

## 19. File-format parsing and provenance

Each unstructured parser converts a format-specific object into a common conceptual unit:

```text
source file + human-readable locator + extracted text
```

Examples:

- PDF → page number;
- DOCX → heading/section context;
- PPTX → slide number;
- invoice image → original filename/OCR text.

Keeping provenance through chunking is what makes later evidence displays meaningful. A chunk without source identity can retrieve relevant text but cannot support a trustworthy citation UI.

## 20. OCR as a fallback, not the default

OCR is slower and more error-prone than extracting embedded text. QueryGuard therefore tries normal PDF/text parsing first and uses Tesseract only when OCR support is installed and a page/image needs it.

OCR output can confuse similar characters, lose layout, or merge columns. This is why invoice OCR accuracy is explicitly not claimed without a labeled scanned-invoice benchmark.

## 21. Semi-structured invoice normalization

An invoice has repeated concepts (number, date, vendor, tax, total) but highly variable layouts. QueryGuard's V1 extraction is a transparent baseline based on labels/aliases and conservative missing-value handling.

The normalized record is useful because analytics questions such as total spend by vendor become ordinary SQL. The raw text remains useful because wording questions such as payment terms are better answered through document retrieval.

This is why invoice mode is hybrid instead of forcing every invoice question through one technique.

## 22. Spreadsheet export safety

CSV/XLSX are not passive text when opened in spreadsheet applications. A text value beginning with characters such as `=`, `+`, `-`, or `@` can be interpreted as a formula.

QueryGuard escapes formula-like **text** before exporting query/invoice results. Numeric negative values remain numeric. The original database is not modified; the protection is applied only to the downloadable representation.

## 23. Provider abstraction without a framework

The project uses a small `TextLLM.complete(...)` interface instead of a large orchestration framework. The benefit is dependency inversion: SQL and document services depend on a behavior, while Ollama/Gemini/Groq own only their HTTP differences.

This makes provider switching a configuration change and keeps business prompts/evaluation outside vendor clients. It also makes mocked unit tests straightforward.

## 24. Why a deterministic demo provider exists

AI systems are difficult to regression-test when every test depends on network availability, changing model behavior, quotas, or credentials. The deterministic demo provider verifies plumbing—API → retrieval → service → database/UI—without pretending to be a real model.

Real model quality is measured separately and must record the exact provider/model/configuration.

## 25. Software correctness vs analytical correctness

There are several different correctness questions:

1. **software correctness** — did parsing/API/validation behave as designed?
2. **SQL validity** — did the model produce parseable/safe SQL?
3. **execution correctness** — did SQL return the same result as a gold query?
4. **semantic correctness** — did the query actually represent user intent?
5. **retrieval quality** — did the right schema/evidence reach the model?

A production-quality evaluation program needs all of them; `pytest` alone cannot establish LLM answer quality.

