from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def database_path() -> Path:
    path = Path("data/chinook/Chinook_Sqlite.sqlite")
    assert path.is_file(), "Run python scripts/setup_chinook.py first."
    return path
