"""Measure schema-table retrieval independently from LLM generation."""

from __future__ import annotations

import json
from pathlib import Path

from queryguard.config import Settings
from queryguard.database.schema import extract_schema
from queryguard.evaluation.metrics import mean, table_recall_at_k
from queryguard.retrieval.lexical import LexicalSchemaRetriever
from queryguard.schema.documents import build_schema_documents


def main() -> None:
    settings = Settings()
    schema = extract_schema(settings.database_path)
    retriever = LexicalSchemaRetriever(build_schema_documents(schema))
    examples = [json.loads(line) for line in Path("data/evaluation/chinook_eval.jsonl").read_text().splitlines() if line.strip()]

    rows = []
    for example in examples:
        results = retriever.search(example["question"], 5)
        names = [result.table for result in results]
        rows.append(
            {
                "id": example["id"],
                "retrieved": names,
                "required": example["required_tables"],
                "recall_at_1": table_recall_at_k(names, example["required_tables"], 1),
                "recall_at_3": table_recall_at_k(names, example["required_tables"], 3),
                "recall_at_5": table_recall_at_k(names, example["required_tables"], 5),
            }
        )

    report = {
        "status": "Measured",
        "scope": "Lexical schema retrieval only; no LLM generation was involved.",
        "examples": len(rows),
        "recall_at_1": mean([r["recall_at_1"] for r in rows]),
        "recall_at_3": mean([r["recall_at_3"] for r in rows]),
        "recall_at_5": mean([r["recall_at_5"] for r in rows]),
        "records": rows,
    }
    output = Path("results/lexical_retrieval_baseline.json")
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
