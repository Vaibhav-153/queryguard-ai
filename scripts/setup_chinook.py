"""Build the bundled Chinook SQLite demo from the verified SQL source."""

from __future__ import annotations

import hashlib
import sqlite3
import urllib.request
from contextlib import closing
from pathlib import Path

VERSION = "v1.4.5"
URL = (
    "https://raw.githubusercontent.com/lerocha/chinook-database/"
    "v1.4.5/ChinookDatabase/DataSources/Chinook_Sqlite.sql"
)

# Git normalizes repository .sql files to LF. Hash the normalized text so the
# same trusted SQL validates on Windows, macOS, Linux, Codespaces, and CI.
EXPECTED_NORMALIZED_SQL_SHA256 = "caf31d698a4a79c628215b552dfe6575e71be052ae02b8f18e763498f55f5d44"

SQL_PATH = Path("data/chinook/Chinook_Sqlite.sql")
DB_PATH = Path("data/chinook/Chinook_Sqlite.sqlite")


def normalized_sha256(path: Path) -> str:
    data = path.read_bytes()
    normalized = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def main() -> None:
    SQL_PATH.parent.mkdir(parents=True, exist_ok=True)

    if not SQL_PATH.exists():
        print(f"Downloading official Chinook {VERSION} SQL source...")
        urllib.request.urlretrieve(URL, SQL_PATH)

    actual = normalized_sha256(SQL_PATH)
    if actual != EXPECTED_NORMALIZED_SQL_SHA256:
        raise RuntimeError(
            "Unexpected Chinook SQL checksum. "
            f"Expected {EXPECTED_NORMALIZED_SQL_SHA256}, got {actual}. "
            "Check the upstream release before proceeding."
        )

    if DB_PATH.exists():
        DB_PATH.unlink()

    with closing(sqlite3.connect(DB_PATH)) as connection:
        connection.executescript(SQL_PATH.read_text(encoding="utf-8-sig"))
        connection.commit()

    print(f"Created {DB_PATH} ({DB_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
