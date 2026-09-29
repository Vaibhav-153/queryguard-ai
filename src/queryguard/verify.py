"""Offline smoke verification exposed as the ``queryguard-verify`` command."""

from pathlib import Path

from queryguard.config import Settings
from queryguard.demo import create_demo_database
from queryguard.query_service import QueryService

QUESTIONS = [
    "Show the top 5 customers by revenue",
    "Which countries generated the most revenue?",
    "How many customers are in the database?",
    "What is the average track price?",
    "Which genres have the most tracks?",
]


def main() -> None:
    database = create_demo_database(Path("data/demo.sqlite"))
    settings = Settings(database_path=database, llm_provider="demo")
    service = QueryService(settings)
    failures = []
    for question in QUESTIONS:
        response = service.ask(question)
        if response.status != "success":
            failures.append(f"{question}: {response.status} - {response.error}")
    if failures:
        raise SystemExit("Verification failed:\n- " + "\n- ".join(failures))
    print(f"Verified {len(QUESTIONS)} demo queries through the governed pipeline.")
