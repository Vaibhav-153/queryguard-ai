# Future Roadmap

Future work is prioritized by actual limitations, not keywords.

## Priority 1 — better evaluation

- larger held-out Text-to-SQL set;
- model comparison across Ollama/Gemini/Groq;
- labeled document QA/citation dataset;
- real anonymized/permissioned invoice benchmark;
- OCR evaluation by scan quality.

## Priority 2 — user-defined spreadsheet relationships

Problem: Excel sheets do not declare foreign keys.

Proposed feature: after upload, let user define `Orders.CustomerId → Customers.CustomerId`. Store relationships in workspace metadata and include them in schema prompts/validation docs.

## Priority 3 — PostgreSQL adapter

Only after the SQLite design is stable. Add a read-only database interface rather than hiding PostgreSQL behind conversion.

## Priority 4 — semantic/hybrid retrieval experiments

Compare lexical, semantic, and simple hybrid scores. Keep only if evaluation shows improvement worth model/download complexity.

## Priority 5 — invoice extraction improvement

- line items;
- OCR confidence;
- template/vendor heuristics;
- optional structured-output LLM extraction;
- human correction screen.

## Priority 6 — durable authenticated workspaces

For real multi-user production:

- authentication;
- object storage;
- encrypted metadata DB;
- tenant isolation;
- scheduled deletion;
- audit logs;
- quotas/rate limiting.

## Not automatically planned

Kafka, Kubernetes, microservices, Redis, or agents. They should be introduced only when load/reliability requirements demonstrate a need.
