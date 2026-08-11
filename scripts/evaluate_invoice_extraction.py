"""Measure heuristic invoice field extraction on hand-authored synthetic examples."""

from __future__ import annotations

import json
from pathlib import Path

from queryguard.invoices.parser import parse_invoice_text

FIELDS = ["invoice_number", "vendor", "currency", "subtotal", "tax", "total"]


def main() -> None:
    path = Path("data/evaluation/synthetic_invoice_eval.jsonl")
    examples = [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]

    correct = 0
    total = 0
    records = []
    for example in examples:
        record = parse_invoice_text(example["source_file"], example["text"])
        predicted = record.model_dump()
        field_results = {}
        for field in FIELDS:
            expected = example["expected"].get(field)
            actual = predicted.get(field)
            matched = actual == expected
            field_results[field] = matched
            correct += int(matched)
            total += 1
        records.append({"id": example["id"], "fields": field_results})

    report = {
        "status": "Measured",
        "scope": "Heuristic extraction on hand-authored synthetic invoice text; not production OCR accuracy.",
        "examples": len(examples),
        "field_exact_match": correct / total if total else 0.0,
        "fields": FIELDS,
        "records": records,
    }
    output = Path("results/invoice_extraction_synthetic.json")
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "records"}, indent=2))


if __name__ == "__main__":
    main()
