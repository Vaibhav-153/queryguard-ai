# Results

This directory stores **measured** evaluation artifacts. It deliberately separates measurements from targets and untested claims.

Current committed artifacts:

- `lexical_retrieval_baseline.json` — table Recall@K over 15 custom Chinook questions.
- `document_retrieval_synthetic.json` — lexical Hit@K over 8 small hand-authored document examples.
- `invoice_extraction_synthetic.json` — heuristic field exact match over 3 small hand-authored invoice examples.
- `build_metadata.json` — final artifact-runtime verification boundary.

The document and invoice sets are smoke/evaluation fixtures, not production benchmarks. Do not present them as real-world accuracy.

For real LLM experiments, use descriptive names such as:

```text
ollama_qwen25coder7b_lexical_20260811.json
gemini35flash_lexical_20260811.json
```

Preserve provider/model, prompt version, retrieval strategy, dataset/split, hardware/runtime, latency, failures, and date with every reported result.
