from queryguard.workspaces import UploadContent, WorkspaceManager


def test_spreadsheet_workspace_lifecycle(settings):
    manager = WorkspaceManager(settings)
    upload = UploadContent("sales.csv", b"region,total\nWest,100\nEast,90\n")
    info = manager.create("spreadsheet", [upload])
    assert info.database_available
    assert info.table_count == 1
    metadata = manager.load(info.workspace_id)
    assert manager.resolve_database(metadata).is_file()
    manager.delete(info.workspace_id)
    assert not (settings.workspace_root / info.workspace_id).exists()


def test_invoice_workspace_has_structured_database(settings):
    manager = WorkspaceManager(settings)
    upload = UploadContent(
        "invoices.csv",
        b"invoice_number,invoice_date,vendor,customer,currency,total\nINV-1,2026-01-01,A,B,INR,500\n",
    )
    info = manager.create("invoice", [upload])
    assert info.invoice_count == 1
    assert info.database_available
