# Architecture

## Design goal

QueryGuard has one frontend and one backend, but it uses **different deterministic pipelines for different source types**. This avoids the weak design of sending every uploaded file directly to an LLM.

## System overview

```mermaid
flowchart TD
    U[User] --> UI[Streamlit UI]
    UI --> API[FastAPI]
    API --> WM[Workspace Manager]

    WM --> S[Structured Pipeline]
    WM --> D[Document Pipeline]
    WM --> I[Invoice Pipeline]

    S --> LLM[Configured LLM]
    D --> LLM
    I --> S
    I --> D

    S --> DB[(Read-only SQLite)]
    API --> LOG[Structured Logs]
```

## Structured pipeline

Used by the Chinook demo, uploaded SQLite, Excel, CSV, and normalized invoices.

```mermaid
sequenceDiagram
    participant U as User
    participant A as FastAPI
    participant R as Schema Retriever
    participant L as LLM
    participant V as SQLGlot Validator
    participant D as SQLite

    U->>A: Natural-language question
    A->>R: Search active schema
    R-->>A: Top-K tables
    A->>L: Question + selected schema
    L-->>A: SQL candidate
    A->>V: Parse AST + enforce policy
    alt unsafe
        V-->>A: Rejected
        A-->>U: Controlled error
    else safe
        V-->>A: Approved tables
        A->>D: Read-only execution
        D-->>A: Rows
        A-->>U: SQL + result + evidence + latency
    end
```

## Spreadsheet ingestion

```mermaid
flowchart LR
    X[XLSX / CSV] --> V[Validate type / archive]
    V --> P[pandas / openpyxl]
    P --> T[Sanitize sheet + column names]
    T --> Q[(Temporary SQLite)]
    Q --> S[Normal Structured Pipeline]
```

Excel is converted rather than creating a second analytics engine. This keeps SQL governance and evaluation reusable.

## Document pipeline

```mermaid
flowchart LR
    F[PDF/DOCX/PPTX] --> P[Parser]
    P --> U[Source-aware Units]
    U --> C[Chunks]
    C --> R[Lexical/Semantic Retrieval]
    R --> E[Top-K Evidence]
    E --> L[LLM]
    L --> A[Grounded Answer]
    E --> CITE[Page/Section/Slide Sources]
```

Document text is explicitly treated as **untrusted data** in the system prompt. Instructions embedded inside a PDF should not override the application instruction.

## Invoice pipeline

```mermaid
flowchart TD
    F[Invoice files] --> P{File type}
    P -->|PDF/Image| X[Text extraction / optional OCR]
    P -->|XLSX/CSV| R[Structured row mapping]
    X --> H[Conservative field parser]
    H --> N[Normalized invoice records]
    R --> N
    N --> DB[(Invoices SQLite)]
    X --> C[Document chunks]
    DB --> SQL[Text-to-SQL analytics]
    C --> QA[Evidence Q&A]
```

This is intentionally hybrid: numerical aggregation is better handled by SQL, while wording such as payment terms is better handled through document evidence.

## Workspace architecture

Uploaded files never replace `data/chinook/Chinook_Sqlite.sqlite`.

```text
data/workspaces/<random-id>/
├── metadata.json
├── uploads/
├── workspace.sqlite          # spreadsheets when applicable
├── invoices.sqlite           # invoice mode when applicable
├── document_chunks.json      # document evidence when applicable
└── invoice_records.json      # normalized invoice fields
```

`WorkspaceManager` creates random UUID-based directories, applies upload limits, persists metadata, expires old workspaces, and never accepts an arbitrary user path.

## LLM provider architecture

```mermaid
flowchart LR
    SQL[SQL Service] --> A[LLMSQLGenerator]
    DOC[Document Service] --> P[TextLLM]
    A --> P
    P --> O[Ollama]
    P --> G[Gemini]
    P --> R[Groq]
    SQL --> DEMO[Demo SQL Generator]
```

The provider interface is intentionally small: `complete(prompt, system_prompt, max_tokens)`. Provider-specific HTTP details stay inside `llm/`.

## Deployment

### Local

```text
Browser → Streamlit :8501 → FastAPI :8000 → Ollama :11434 / hosted provider
```

### Hosted portfolio demo

```text
Browser
  ↓
Streamlit Community Cloud
  ↓ HTTPS + shared QueryGuard key
Render FastAPI
  ↓
Gemini API
```

Uploaded workspaces on a free hosted service are temporary. The local/Docker path is the reproducible primary path for private files.

## Failure handling

- invalid upload → HTTP 400 with reason;
- oversized upload → HTTP 413;
- expired workspace → HTTP 404 and re-upload instruction;
- missing provider key → HTTP 503 rather than a fake answer;
- unsafe SQL → `blocked` response;
- ordinary invalid SQL → one repair attempt, then error;
- query timeout → controlled database error;
- no document evidence → explicit unsupported answer;
- OCR unavailable → clear dependency message;
- invoice uncertainty → `needs_review=true` instead of guessing silently.
