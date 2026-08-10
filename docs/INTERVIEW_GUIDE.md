# Interview guide

## 30-second explanation

QueryGuard AI is a governed Text-to-SQL analytics copilot. A user asks a business question, the system retrieves relevant schema context, uses a local Ollama model to propose SQL, parses that SQL with SQLGlot, blocks unsafe or unapproved statements, executes approved queries through read-only SQLite, and returns verified rows. I also built retrieval and execution evaluation so I can measure components instead of assuming they help.

## 60-second explanation

The main design decision was to treat model output as untrusted. Prompt instructions alone are not security, so generated SQL goes through AST validation and an independent read-only database connection. I first built a transparent lexical schema retriever and measured table Recall@K, then added an optional Sentence Transformer retriever for semantic comparison. I also distinguish ambiguous user requests from executable ones and allow only one correction attempt for normal failures. The repository includes FastAPI, Streamlit, pytest tests, Docker, CI, data provenance, and a saved evaluation format.

## Common technical questions

### Why SQLGlot instead of regex?
SQL is a grammar with nesting, comments, CTEs and dialect details. Regex can detect some obvious words but is not a structural policy engine. An AST lets the code inspect statement and table nodes explicitly.

### Why is SQLite read-only mode still needed after validation?
Defense in depth. A validator bug or parser edge case should not automatically become write access.

### Why not send the full schema?
It is acceptable as a baseline for tiny schemas, but irrelevant columns increase prompt length and ambiguity. Retrieval becomes more important as schemas grow.

### Why no vector database?
The schema is small. Exact cosine search is simpler and measurable. I would add FAISS or a vector service only after scale data justified it.

### Why only one repair attempt?
Unbounded self-correction can hide failures, increase latency, and make behavior unpredictable. One attempt is easy to evaluate and reason about.

### Does safe SQL mean correct SQL?
No. Safety, executability and semantic correctness are different properties. The evaluation runner compares executed results against gold SQL where possible.

### What would you change for PostgreSQL production use?
Use a dedicated read-only role, database-native statement timeouts, connection pooling, explicit schema permissions, authenticated users, row/column policies, audit logs, and PostgreSQL-specific SQLGlot dialect tests.

## Debugging story to prepare

Use a real experiment from `results/` after running Ollama. Explain one failure where schema retrieval missed a required table or the LLM chose the wrong join, how you reproduced it, what signal showed the cause, what change you made, and whether metrics improved. Do not invent a failure percentage.

## Five-minute demo

1. Open architecture diagram (30 sec).
2. Ask “Show the top 5 customers by revenue” (60 sec).
3. Show retrieved tables and generated SQL (45 sec).
4. Show governance status and read-only result (45 sec).
5. Ask “Who are the best customers?” to demonstrate clarification (30 sec).
6. Show a blocked destructive SQL unit test (45 sec).
7. Open `results/` and explain measured vs untested metrics (45 sec).

Backup if the model is unavailable: run demo provider, clearly label it as deterministic smoke mode, then show saved real-model evaluation only if one was actually produced earlier.
