# Evaluation and Honest Reporting

## Status labels

Use these labels consistently:

- **Measured** — command executed with recorded data/configuration.
- **Target** — desired result, not yet observed.
- **Estimated** — reasoned estimate, not benchmark evidence.
- **Not tested** — implementation exists but was not executed in that environment.
- **Not available** — cannot currently be measured.

## 1. Schema retrieval

Command:

```bash
python scripts/evaluate_retrieval.py
```

Dataset: 15 project-specific Chinook questions.

Metrics:

- table Recall@1;
- table Recall@3;
- table Recall@5.

Current measured artifact values:

```text
Recall@1 = 0.800
Recall@3 = 0.967
Recall@5 = 0.967
```

This is **retrieval only**. It says nothing directly about final LLM SQL accuracy.

## 2. Text-to-SQL execution evaluation

Command:

```bash
python -m queryguard.evaluation.runner \
  --provider ollama \
  --retrieval lexical \
  --output results/ollama_lexical.json
```

The runner records:

- successful execution rate;
- execution match against gold query result;
- table Recall@3/5;
- mean/p95 latency;
- repair rate;
- generated SQL and failure category.

Do not optimize repeatedly against a result file and still call it an untouched final evaluation.

## 3. Document retrieval

Command:

```bash
python scripts/evaluate_document_retrieval.py
```

Current synthetic result:

```text
Hit@1 = 0.875
Hit@3 = 0.875
```

This set is hand-authored and tiny. Its purpose is component regression/failure analysis.

## 4. Invoice extraction

Command:

```bash
python scripts/evaluate_invoice_extraction.py
```

Current synthetic result:

```text
Field exact match = 1.000
```

Scope: 3 simple text invoices × 6 expected fields. It does not measure OCR, line items, diverse layouts, or real vendor documents.

## 5. Security metrics

For a curated test suite, report:

- unsafe-query rejection count/rate;
- safe-query false rejection count;
- parser failures.

A target such as 100% rejection is not a measured claim until the suite has run.

## 6. Performance

If reporting latency, also record:

- hardware;
- provider/model;
- local vs hosted;
- network context;
- retrieval strategy;
- number/size of documents;
- database size.

A Render/Gemini latency should not be compared directly with local Ollama latency without context.

## Experiment log template

```text
Experiment ID:
Date:
Hypothesis:
Change:
Provider/model:
Retrieval:
Dataset:
Metric:
Result:
Interpretation:
Decision:
Next action:
```

Negative results are useful evidence. The current lexical document retrieval miss is intentionally preserved in the report.
