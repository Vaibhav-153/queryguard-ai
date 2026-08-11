import sqlite3
from contextlib import closing

from queryguard.config import Settings
from queryguard.workspaces.manager import UploadContent, WorkspaceManager


def test_invoice_csv_workspace_creates_analytics_database(tmp_path):
    csv_data = (
        b"invoice_number,vendor,invoice_date,currency,total\n"
        b"INV-1,Alpha Supplies,2026-01-02,USD,120.50\n"
        b"INV-2,Beta Services,2026-01-05,USD,80.00\n"
    )

    manager = WorkspaceManager(
        Settings(
            environment="test",
            workspace_root=tmp_path / "workspaces",
            llm_provider="demo",
        )
    )
    info = manager.create(
        "invoice",
        [UploadContent(name="invoices.csv", content=csv_data)],
    )

    assert info.invoice_count == 2
    assert info.database_available is True

    metadata = manager.load(info.workspace_id)
    database_path = manager.resolve_database(metadata)
    with closing(sqlite3.connect(database_path)) as connection:
        total = connection.execute("SELECT SUM(total) FROM invoices").fetchone()[0]

    assert round(total, 2) == 200.50
