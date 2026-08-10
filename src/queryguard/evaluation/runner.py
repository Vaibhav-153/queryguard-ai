"""Run a reproducible evaluation over the custom Chinook set."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from queryguard.config import Settings
from queryguard.database.connection import execute_read_only
from queryguard.evaluation.metrics import mean, percentile, result_match, table_recall_at_k
from queryguard.logging_config import configure_logging
from queryguard.services.query_service import QueryService


def load_examples(path: Path) -> list[dict]:
    examples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            examples.append(json.loads(line))
    return examples


def run_evaluation(settings: Settings, dataset_path: Path, max_examples: int | None = None) -> dict:
    service = QueryService(settings)
    examples = load_examples(dataset_path)
    if max_examples is not None:
        examples = examples[:max_examples]

    records = []
    for example in examples:
        response = service.ask(example["question"])
        retrieved = [item.table for item in response.retrieved_tables]
        recall_at_3 = table_recall_at_k(retrieved, example["required_tables"], 3)
        recall_at_5 = table_recall_at_k(retrieved, example["required_tables"], 5)

        execution_match = False
        if response.status == "success":
            gold = execute_read_only(
                settings.database_path,
                example["gold_sql"],
                max_rows=settings.max_result_rows,
                timeout_ms=settings.query_timeout_ms,
            )
            execution_match = result_match(
                response.columns,
                response.rows,
                gold.columns,
                gold.rows,
                bool(example.get("order_sensitive", False)),
            )

        records.append(
            {
                "id": example["id"],
                "category": example["category"],
                "status": response.status,
                "execution_match": execution_match,
                "table_recall_at_3": recall_at_3,
                "table_recall_at_5": recall_at_5,
                "total_latency_ms": response.latency_ms.get("total", 0.0),
                "repaired": response.repaired,
                "generated_sql": response.sql,
                "error": response.error,
            }
        )

    latencies = [float(record["total_latency_ms"]) for record in records]
    summary = {
        "examples": len(records),
        "successful_execution_rate": mean([1.0 if r["status"] == "success" else 0.0 for r in records]),
        "execution_match_rate": mean([1.0 if r["execution_match"] else 0.0 for r in records]),
        "table_recall_at_3": mean([float(r["table_recall_at_3"]) for r in records]),
        "table_recall_at_5": mean([float(r["table_recall_at_5"]) for r in records]),
        "mean_latency_ms": mean(latencies),
        "p95_latency_ms": percentile(latencies, 0.95),
        "repair_rate": mean([1.0 if r["repaired"] else 0.0 for r in records]),
    }
    return {
        "metadata": {
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model_name,
            "retrieval_strategy": settings.retrieval_strategy,
            "dataset": str(dataset_path),
            "note": "Metrics are measured only for this run and configuration.",
        },
        "summary": summary,
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("data/evaluation/chinook_eval.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("results/latest_evaluation.json"))
    parser.add_argument("--provider", choices=["ollama", "gemini", "groq", "demo"], default=None)
    parser.add_argument("--retrieval", choices=["lexical", "semantic"], default=None)
    parser.add_argument("--max-examples", type=int, default=None)
    args = parser.parse_args()

    settings = Settings()
    updates = {}
    if args.provider:
        updates["llm_provider"] = args.provider
    if args.retrieval:
        updates["retrieval_strategy"] = args.retrieval
    if updates:
        settings = settings.model_copy(update=updates)

    configure_logging(settings.log_level)
    report = run_evaluation(settings, args.dataset, args.max_examples)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
