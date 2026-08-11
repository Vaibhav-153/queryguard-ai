# Interview Guide

## 30-second explanation

“QueryGuard AI is a governed data and document analytics platform. For databases and spreadsheets, it retrieves relevant schema, uses an LLM to generate SQL, validates that SQL structurally with SQLGlot, and executes only through a read-only SQLite connection. For PDF, Word, and PowerPoint it uses evidence retrieval and returns source locations. I also added invoice extraction that normalizes fields into SQLite while retaining document text. It runs with local Ollama or hosted Gemini/Groq and includes component evaluation, security tests, Docker, CI, and full documentation.”

## 60-second explanation

Start with the problem: LLM-generated SQL can be unsafe/wrong and document answers can hallucinate. Explain the two pipelines: structured Text-to-SQL and unstructured RAG. Mention workspaces so Chinook is only a demo rather than a hardcoded dependency. Explain AST validation + read-only DB as defense in depth. Mention measured retrieval metrics and honest untested model/OCR claims.

## 3-minute explanation outline

1. Problem/users.
2. Original Chinook baseline.
3. Schema retrieval.
4. SQL generation + SQLGlot + read-only execution.
5. Dynamic upload workspace.
6. Excel/CSV reuse through SQLite conversion.
7. document source-aware RAG.
8. invoice hybrid architecture.
9. Ollama/Gemini/Groq provider abstraction.
10. tests/evaluation/limitations.

## Design questions

### Why not let the LLM execute SQL directly?

Prompts are probabilistic and not a security boundary. I separate generation from validation/execution. SQLGlot checks structure and referenced tables; SQLite is opened independently in read-only mode.

### Why SQLGlot instead of regex?

SQL has nesting, CTEs, aliases, comments, and dialect details. Regex cannot reliably understand the query tree. An AST lets me detect operation node types and physical table references.

### Why convert Excel to SQLite?

It reuses the same proven analytics path: schema extraction, retrieval, validation, time/row limits, evaluation, and exports. A second pandas-only NL query engine would duplicate logic and governance.

### Why not convert PDF to SQL too?

PDF paragraphs/pages are unstructured evidence, not naturally relational rows. RAG preserves page/section context and is a better abstraction for textual questions.

### Why no agent?

The workflow is deterministic: retrieve → generate → validate → execute. An open-ended agent loop would add latency, cost, and harder failure analysis without a requirement. I allow only one bounded SQL repair attempt.

### Why lexical retrieval if embeddings exist?

It is reproducible, cheap, explainable, and performs strongly on the small Chinook schema. Semantic retrieval is optional and useful for vocabulary mismatch, demonstrated by a known lexical document failure.

### How would you scale schema retrieval?

At current scale, linear ranking is trivial. With thousands/millions of schema/document vectors, I would persist embeddings and introduce an ANN index such as FAISS or a suitable vector-capable database after measuring the need.

### How do you know an answer is correct?

I separate claims. For SQL, execution against the real database proves the displayed rows came from that SQL, not that the SQL perfectly matches intent. I use gold-result execution match in evaluation. For documents, I return retrieved evidence and evaluate retrieval separately; LLM answer correctness still needs labeled evaluation/human review.

### What happens without foreign keys?

QueryGuard still knows table/column names but does not invent declared relationships. For Excel, that is a known limitation. A future UI could let the user define relationships explicitly.

### What if an uploaded PDF says “ignore the system prompt”?

Document content is marked untrusted in the system prompt. Retrieval returns evidence as data. This reduces risk but does not guarantee model-level prompt-injection immunity; production would add more policy/testing layers.

### Why multiple LLM providers?

It solves deployment/privacy constraints: Ollama enables local/offline use, Gemini enables a lightweight public demo, Groq is an alternative, and demo mode keeps CI deterministic. The application logic is provider-independent.

## Debugging stories

### Chinook checksum failure in Codespaces

Symptom: SQL checksum differed across environments.

Root cause: Git normalized `.sql` to LF, so raw byte hashes differed from the original source representation.

Fix: normalize CRLF/CR to LF before hashing. Keep validation instead of deleting the checksum.

Learning: reproducibility checks must account for text normalization.

### Render/Streamlit access-key mismatch

Symptom: Streamlit could reach the API but `/query` returned 401.

Root cause: hosted services loaded different shared-secret values / stale deployments.

Fix: make `QUERYGUARD_API_ACCESS_KEY` an explicitly entered `sync:false` secret, save/deploy Render, reboot Streamlit, keep Gemini key only on backend.

Learning: connectivity and authentication failures are different layers; `/health` helped isolate them.

### Ruff CI failures

Symptom: deployment worked but GitHub Actions was red before tests.

Fix: move formatting/import cleanup into local/Codespaces workflow and make CI check, not silently auto-fix committed source.

Learning: CI should detect source quality regression, not modify repository state.

## Security questions

### Can an attacker upload `../../secret.db`?

Server uses `Path(name).name` plus filename sanitization and writes only inside a server-generated workspace directory.

### Can a generated query `DROP TABLE`?

SQLGlot rejects it, and the SQLite connection is independently read-only.

### Is `X-QueryGuard-Key` real authentication?

No. It is a shared-secret protection suitable for a portfolio frontend/backend pair. Production needs user identity/authentication/authorization.

## Failure/limitation questions

### Biggest current limitation?

AI semantic correctness and uploaded-data ambiguity. Safe execution does not guarantee correct business interpretation. Excel relationship metadata is also weak, and invoice extraction is only an explainable baseline.

### A negative experiment/result?

Lexical document retrieval misses one synthetic password-length question because the wording differs from evidence. I kept the miss and documented semantic retrieval as the appropriate improvement rather than rewriting the benchmark to make it perfect.

## DSA/CS quick questions

- Why sets for table allowlists? O(1) average membership and deduplication.
- Why dictionary/hash map for schema lookup? Efficient table-name lookup.
- Where is a graph present? Foreign-key relationships between tables.
- Top-K retrieval complexity? Current linear scoring O(N) over schema/chunks plus sorting O(N log N); sufficient for small personal indexes.
- Why UUID workspace IDs? Non-user-controlled identifiers with negligible collision probability for this scope.
