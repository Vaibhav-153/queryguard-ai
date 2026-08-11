"""Run a small deterministic offline evaluation suitable for CI smoke checks."""

from pathlib import Path

from queryguard.config import Settings
from queryguard.evaluation.runner import run_evaluation

if __name__ == "__main__":
    settings = Settings(llm_provider="demo", retrieval_strategy="lexical")
    report = run_evaluation(settings, Path("data/evaluation/chinook_eval.jsonl"), max_examples=6)
    print(report["summary"])
