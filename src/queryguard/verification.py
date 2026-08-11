"""Fast local smoke verification used after a fresh clone."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from queryguard.config import Settings
from queryguard.database.schema import extract_schema

EXPECTED_CUSTOMERS = 59
EXPECTED_TRACKS = 3503
EXPECTED_REVENUE = 2328.60


def verify_demo_database(path: Path) -> list[str]:
    messages: list[str] = []
    if not path.is_file():
        raise RuntimeError(f"Demo database is missing: {path}")

    with closing(sqlite3.connect(path)) as connection:
        quick_check = connection.execute("PRAGMA quick_check").fetchone()[0]
        customers = connection.execute("SELECT COUNT(*) FROM Customer").fetchone()[0]
        tracks = connection.execute("SELECT COUNT(*) FROM Track").fetchone()[0]
        revenue = connection.execute("SELECT ROUND(SUM(Total), 2) FROM Invoice").fetchone()[0]

    if quick_check != "ok":
        raise RuntimeError(f"SQLite quick_check failed: {quick_check}")
    if customers != EXPECTED_CUSTOMERS:
        raise RuntimeError(f"Unexpected customer count: {customers}")
    if tracks != EXPECTED_TRACKS:
        raise RuntimeError(f"Unexpected track count: {tracks}")
    if float(revenue) != EXPECTED_REVENUE:
        raise RuntimeError(f"Unexpected invoice revenue: {revenue}")

    schema = extract_schema(path)
    messages.append(f"database=ok tables={len(schema)}")
    messages.append(f"customers={customers} tracks={tracks} revenue={revenue:.2f}")
    return messages


def main() -> None:
    settings = Settings()
    messages = verify_demo_database(settings.database_path)
    print("QueryGuard smoke verification passed")
    for message in messages:
        print(f"- {message}")
    print(f"- provider={settings.llm_provider} model={settings.llm_model_name}")


if __name__ == "__main__":
    main()
