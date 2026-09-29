# Evaluation

The repository keeps evaluation deliberately small and reproducible. It does not claim general Text-to-SQL accuracy from the bundled demo.

## Schema retrieval check

Run:

```bash
python scripts/evaluate_retrieval.py
```

The script uses five declared questions against the synthetic three-table demo database. Each question lists the table or tables expected to be available to SQL generation.

Current output:

| Metric | Result |
| --- | ---: |
| Mean Recall@1 | 0.800 |
| Mean Recall@3 | 1.000 |
| Mean Recall@5 | 1.000 |

The detailed ranking for every question is stored in `results/retrieval_metrics.json`.

For two revenue questions, both `Customer` and `Invoice` are required. Only one table can occupy rank 1, so Recall@1 for those cases is 0.5 even when the other required table is ranked second. Recall@3 is therefore the more useful check for this tiny schema.

## Demo pipeline verification

Run:

```bash
queryguard-verify
```

This sends five bundled questions through schema retrieval, deterministic SQL generation, SQL validation and read-only execution. It checks that the complete local pipeline returns a successful response.

## What is not measured

The repository does not report general LLM accuracy, execution accuracy on external databases, document-answer factual accuracy, or invoice OCR accuracy. Those would require larger labeled evaluation sets and, for model providers, fixed provider/model versions.
