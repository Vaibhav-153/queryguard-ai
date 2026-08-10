"""Download the official Chinook SQL script and build the SQLite demo database."""

from __future__ import annotations

import hashlib
import sqlite3
import urllib.request
from pathlib import Path

VERSION = "v1.4.5"
URL = "https://raw.githubusercontent.com/lerocha/chinook-database/v1.4.5/ChinookDatabase/DataSources/Chinook_Sqlite.sql"
EXPECTED_SQL_SHA256 = "fdcb271b3e9c840216b09168752bddca973ed3917b40e49b603b15831114aea1"
SQL_PATH = Path("data/chinook/Chinook_Sqlite.sql")
DB_PATH = Path("data/chinook/Chinook_Sqlite.sqlite")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    SQL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not SQL_PATH.exists():
        print(f"Downloading official Chinook {VERSION} SQL source...")
        urllib.request.urlretrieve(URL, SQL_PATH)

    actual = sha256(SQL_PATH)
    if actual != EXPECTED_SQL_SHA256:
        raise RuntimeError(
            f"Unexpected Chinook SQL checksum. Expected {EXPECTED_SQL_SHA256}, got {actual}. "
            "Check the upstream release before proceeding."
        )

    if DB_PATH.exists():
        DB_PATH.unlink()
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.executescript(SQL_PATH.read_text(encoding="utf-8-sig"))
        connection.commit()
    finally:
        connection.close()
    print(f"Created {DB_PATH} ({DB_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
