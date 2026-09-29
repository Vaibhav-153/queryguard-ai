"""Measure lexical schema retrieval on a small transparent demo question set."""

from __future__ import annotations

import json
from pathlib import Path

from queryguard.database import extract_schema
from queryguard.demo import create_demo_database
from queryguard.retrieval import LexicalSchemaRetriever

CASES = [
    ("Show the top customers by revenue", {"Customer", "Invoice"}),
    ("Which countries generated the most revenue?", {"Customer", "Invoice"}),
    ("How many customers are in the database?", {"Customer"}),
    ("What is the average track price?", {"Track"}),
    ("Which genres have the most tracks?", {"Track"}),
]


def recall_at(results: list[str], expected: set[str], k: int) -> float:
    retrieved = set(results[:k])
    return len(retrieved & expected) / len(expected)


def main() -> None:
    database = create_demo_database(Path("data/demo.sqlite"))
    retriever = LexicalSchemaRetriever(extract_schema(database))
    rows = []
    recalls = {1: [], 3: [], 5: []}
    for question, expected in CASES:
        ranked = [item.table for item in retriever.search(question, 5)]
        row = {"question": question, "expected": sorted(expected), "retrieved": ranked}
        for k in recalls:
            value = recall_at(ranked, expected, k)
            row[f"recall_at_{k}"] = value
            recalls[k].append(value)
        rows.append(row)
    summary = {
        "evaluation_set": "five synthetic demo questions stored in scripts/evaluate_retrieval.py",
        "case_count": len(CASES),
        "mean_recall_at_1": round(sum(recalls[1]) / len(recalls[1]), 3),
        "mean_recall_at_3": round(sum(recalls[3]) / len(recalls[3]), 3),
        "mean_recall_at_5": round(sum(recalls[5]) / len(recalls[5]), 3),
        "cases": rows,
    }
    output = Path("results/retrieval_metrics.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main()
