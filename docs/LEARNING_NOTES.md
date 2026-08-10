# Learning notes

## Concepts to understand before interviews

### SQL
- joins vs correlated subqueries;
- `GROUP BY` and aggregates;
- CTEs;
- indexes and query plans;
- why two different SQL strings can return the same answer.

### Generative AI
- prompt context vs model weights;
- temperature and deterministic evaluation;
- retrieval Recall@K;
- why model output must be treated as untrusted input;
- benchmark contamination.

### Backend
- HTTP request/response validation;
- dependency boundaries;
- configuration through environment variables;
- controlled exceptions vs raw stack traces;
- health checks.

### Security
- least privilege;
- defense in depth;
- allowlists;
- parser/AST validation;
- resource exhaustion from read-only queries.

## Mini assignments

1. Add a new ambiguity rule with tests.
2. Add Mean Reciprocal Rank to `evaluation/metrics.py`.
3. Create five new Chinook evaluation questions without looking at model output first.
4. Run lexical and semantic retrieval and write one paragraph explaining failures.
5. Add a PostgreSQL executor behind the same interface without changing QueryService behavior.

## Review checklist

You should be able to explain every file under `src/queryguard`, why each dependency exists, what happens when Ollama is offline, why dangerous SQL is not repaired, and why valid SQL is not equivalent to a correct business answer.
