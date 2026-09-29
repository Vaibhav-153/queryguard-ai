from pathlib import Path

import pytest

from queryguard.config import Settings
from queryguard.demo import create_demo_database


@pytest.fixture()
def demo_db(tmp_path: Path) -> Path:
    return create_demo_database(tmp_path / "demo.sqlite")


@pytest.fixture()
def settings(tmp_path: Path, demo_db: Path) -> Settings:
    return Settings(
        environment="test",
        database_path=demo_db,
        workspace_root=tmp_path / "workspaces",
        llm_provider="demo",
        max_upload_mb=5,
        max_total_upload_mb=10,
        max_upload_files=3,
    )
