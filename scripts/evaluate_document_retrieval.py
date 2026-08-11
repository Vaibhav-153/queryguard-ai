"""Measure lexical retrieval on a small hand-authored synthetic document set."""

from __future__ import annotations

import json
from pathlib import Path

from queryguard.documents.models import DocumentChunk
from queryguard.documents.retrieval import LexicalDocumentRetriever
from queryguard.evaluation.metrics import mean


def main() -> None:
    chunk_path = Path("data/evaluation/synthetic_document_chunks.jsonl")
    eval_path = Path("data/evaluation/synthetic_document_eval.jsonl")

    chunks = [
        DocumentChunk.from_dict(json.loads(line))
        for line in chunk_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    examples = [
        json.loads(line)
        for line in eval_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    retriever = LexicalDocumentRetriever(chunks)
    records = []
    for example in examples:
        hits = retriever.search(example["question"], 3)
        retrieved = [hit.chunk.chunk_id for hit in hits]
        required = set(example["required_chunks"])
        records.append(
            {
                "id": example["id"],
                "retrieved": retrieved,
                "hit_at_1": float(bool(set(retrieved[:1]) & required)),
                "hit_at_3": float(bool(set(retrieved[:3]) & required)),
            }
        )

    report = {
        "status": "Measured",
        "scope": "Lexical document retrieval on a small hand-authored synthetic evaluation set.",
        "examples": len(records),
        "hit_at_1": mean([record["hit_at_1"] for record in records]),
        "hit_at_3": mean([record["hit_at_3"] for record in records]),
        "records": records,
    }
    output = Path("results/document_retrieval_synthetic.json")
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
