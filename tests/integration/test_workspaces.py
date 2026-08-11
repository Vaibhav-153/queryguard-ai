import sqlite3
from contextlib import closing

import pandas as pd
import pytest

from queryguard.config import Settings
from queryguard.ingestion.common import IngestionError
from queryguard.workspaces.manager import UploadContent, WorkspaceManager


def test_database_workspace_uses_uploaded_sqlite(tmp_path):
    source = tmp_path / "custom.sqlite"
    with closing(sqlite3.connect(source)) as connection:
        connection.execute("CREATE TABLE products(id INTEGER PRIMARY KEY, name TEXT, revenue REAL)")
        connection.execute("INSERT INTO products(name, revenue) VALUES ('A', 10.0)")
        connection.commit()

    manager = WorkspaceManager(
        Settings(
            environment="test",
            workspace_root=tmp_path / "workspaces",
            llm_provider="demo",
        )
    )
    info = manager.create(
        "database",
        [UploadContent(name="custom.sqlite", content=source.read_bytes())],
    )
    assert info.database_available is True
    assert info.table_count == 1
    assert info.column_count == 3


def test_spreadsheet_workspace_converts_excel(tmp_path):
    source = tmp_path / "sales.xlsx"
    with pd.ExcelWriter(source, engine="openpyxl") as writer:
        pd.DataFrame({"customer": ["A", "B"], "revenue": [10, 20]}).to_excel(
            writer,
            sheet_name="Sales",
            index=False,
        )

    manager = WorkspaceManager(
        Settings(
            environment="test",
            workspace_root=tmp_path / "workspaces",
            llm_provider="demo",
        )
    )
    info = manager.create(
        "spreadsheet",
        [UploadContent(name="sales.xlsx", content=source.read_bytes())],
    )
    assert info.database_available is True
    assert info.table_count == 1
    assert info.column_count == 2


def test_workspace_manager_enforces_combined_upload_limit(tmp_path):
    manager = WorkspaceManager(
        Settings(
            environment="test",
            workspace_root=tmp_path / "workspaces",
            llm_provider="demo",
            max_total_upload_mb=1,
        )
    )

    with pytest.raises(IngestionError, match="combined upload"):
        manager.create(
            "document",
            [
                UploadContent(name="one.pdf", content=b"a" * 700_000),
                UploadContent(name="two.pdf", content=b"b" * 700_000),
            ],
        )


def test_workspace_manager_enforces_file_count_limit(tmp_path):
    manager = WorkspaceManager(
        Settings(
            environment="test",
            workspace_root=tmp_path / "workspaces",
            llm_provider="demo",
            max_upload_files=1,
        )
    )

    with pytest.raises(IngestionError, match="At most 1 files"):
        manager.create(
            "document",
            [
                UploadContent(name="one.pdf", content=b"a"),
                UploadContent(name="two.pdf", content=b"b"),
            ],
        )
