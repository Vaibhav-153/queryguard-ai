"""Ephemeral filesystem-backed workspaces for uploaded sources."""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from queryguard.config import Settings
from queryguard.database import extract_schema
from queryguard.documents import save_chunks
from queryguard.ingestion import (
    DOCUMENT_EXTENSIONS,
    INVOICE_EXTENSIONS,
    SPREADSHEET_EXTENSIONS,
    SQLITE_EXTENSIONS,
    IngestionError,
    extract_document_chunks,
    safe_filename,
    spreadsheet_to_sqlite,
    validate_sqlite_database,
)
from queryguard.invoices import parse_invoice_file, save_invoice_records, write_invoice_database
from queryguard.models import WorkspaceInfo


@dataclass(frozen=True, slots=True)
class UploadContent:
    name: str
    content: bytes


@dataclass(slots=True)
class WorkspaceMetadata:
    workspace_id: str
    kind: str
    display_name: str
    source_files: list[str]
    created_at: str
    expires_at: str
    database_file: str | None = None
    chunks_file: str | None = None
    invoices_file: str | None = None
    table_count: int = 0
    column_count: int = 0
    relationship_count: int = 0
    document_chunk_count: int = 0
    invoice_count: int = 0
    warnings: list[str] | None = None


class WorkspaceNotFoundError(RuntimeError):
    pass


class WorkspaceManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.workspace_root
        self.root.mkdir(parents=True, exist_ok=True)

    def _dir(self, workspace_id: str) -> Path:
        if len(workspace_id) != 32 or any(char not in "0123456789abcdef" for char in workspace_id):
            raise WorkspaceNotFoundError("Invalid workspace identifier.")
        return self.root / workspace_id

    def _metadata_path(self, workspace_id: str) -> Path:
        return self._dir(workspace_id) / "metadata.json"

    def cleanup_expired(self) -> int:
        removed = 0
        now = datetime.now(UTC)
        if not self.root.exists():
            return 0
        for directory in self.root.iterdir():
            metadata_path = directory / "metadata.json"
            if not directory.is_dir() or not metadata_path.exists():
                continue
            try:
                payload = json.loads(metadata_path.read_text(encoding="utf-8"))
                expires = datetime.fromisoformat(payload["expires_at"])
            except Exception:
                continue
            if expires < now:
                shutil.rmtree(directory, ignore_errors=True)
                removed += 1
        return removed

    def create(self, kind: str, uploads: list[UploadContent]) -> WorkspaceInfo:
        if kind not in {"database", "spreadsheet", "document", "invoice"}:
            raise IngestionError(f"Unsupported workspace kind: {kind}")
        if not uploads:
            raise IngestionError("At least one file is required.")
        if len(uploads) > self.settings.max_upload_files:
            raise IngestionError(f"At most {self.settings.max_upload_files} files can be uploaded at once.")
        if sum(len(upload.content) for upload in uploads) > self.settings.max_total_upload_bytes:
            raise IngestionError("Combined upload exceeds the configured workspace limit.")
        if kind in {"database", "spreadsheet"} and len(uploads) != 1:
            raise IngestionError(f"{kind.title()} mode accepts one source file at a time.")

        self.cleanup_expired()
        workspace_id = uuid.uuid4().hex
        directory = self.root / workspace_id
        uploads_dir = directory / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=False)
        try:
            paths = self._store_uploads(uploads_dir, uploads)
            metadata = self._build_metadata(workspace_id, kind, directory, paths)
            (directory / "metadata.json").write_text(
                json.dumps(asdict(metadata), indent=2), encoding="utf-8"
            )
            return self.to_info(metadata)
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise

    def _store_uploads(self, directory: Path, uploads: list[UploadContent]) -> list[Path]:
        stored: list[Path] = []
        for upload in uploads:
            if len(upload.content) > self.settings.max_upload_bytes:
                raise IngestionError(f"{upload.name} exceeds the per-file upload limit.")
            name = safe_filename(upload.name)
            path = directory / name
            if path.exists():
                path = directory / f"{path.stem}_{len(stored) + 1}{path.suffix}"
            path.write_bytes(upload.content)
            stored.append(path)
        return stored

    def _build_metadata(self, workspace_id: str, kind: str, directory: Path, paths: list[Path]) -> WorkspaceMetadata:
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=self.settings.workspace_ttl_minutes)
        warnings: list[str] = []
        database_file: str | None = None
        chunks_file: str | None = None
        invoices_file: str | None = None
        invoice_count = 0
        chunk_count = 0

        if kind == "database":
            path = paths[0]
            if path.suffix.lower() not in SQLITE_EXTENSIONS:
                raise IngestionError("Database mode accepts .db, .sqlite, or .sqlite3 files.")
            validate_sqlite_database(path)
            database_file = str(path.relative_to(directory))
        elif kind == "spreadsheet":
            path = paths[0]
            if path.suffix.lower() not in SPREADSHEET_EXTENSIONS:
                raise IngestionError("Spreadsheet mode accepts .csv or .xlsx files.")
            database_path = directory / "workspace.sqlite"
            warnings.extend(
                spreadsheet_to_sqlite(
                    path,
                    database_path,
                    self.settings.max_office_uncompressed_bytes,
                )
            )
            database_file = str(database_path.relative_to(directory))
        elif kind == "document":
            chunks = []
            for path in paths:
                if path.suffix.lower() not in DOCUMENT_EXTENSIONS:
                    raise IngestionError("Document mode accepts .pdf, .docx, or .pptx files.")
                parsed, parsed_warnings = extract_document_chunks(
                    path, self.settings.max_office_uncompressed_bytes
                )
                chunks.extend(parsed)
                warnings.extend(parsed_warnings)
            if not chunks:
                raise IngestionError("No usable document text was extracted.")
            chunks_path = directory / "document_chunks.json"
            save_chunks(chunks, chunks_path)
            chunks_file = chunks_path.name
            chunk_count = len(chunks)
        else:
            records = []
            chunks = []
            for path in paths:
                if path.suffix.lower() not in INVOICE_EXTENSIONS:
                    raise IngestionError("Invoice mode accepts PDF, image, CSV, or XLSX files.")
                parsed_records, parsed_chunks, parsed_warnings = parse_invoice_file(
                    path, self.settings.max_office_uncompressed_bytes
                )
                records.extend(parsed_records)
                chunks.extend(parsed_chunks)
                warnings.extend(parsed_warnings)
            if not records:
                raise IngestionError("No invoice records could be extracted.")
            database_path = directory / "invoices.sqlite"
            write_invoice_database(records, database_path)
            records_path = directory / "invoice_records.json"
            save_invoice_records(records, records_path)
            database_file = database_path.name
            invoices_file = records_path.name
            invoice_count = len(records)
            if chunks:
                chunks_path = directory / "invoice_chunks.json"
                save_chunks(chunks, chunks_path)
                chunks_file = chunks_path.name
                chunk_count = len(chunks)

        table_count = column_count = relationship_count = 0
        if database_file:
            schema = extract_schema(directory / database_file)
            table_count = len(schema)
            column_count = sum(len(table.columns) for table in schema)
            relationship_count = sum(len(table.foreign_keys) for table in schema)

        return WorkspaceMetadata(
            workspace_id=workspace_id,
            kind=kind,
            display_name=paths[0].name if len(paths) == 1 else f"{len(paths)} uploaded files",
            source_files=[path.name for path in paths],
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            database_file=database_file,
            chunks_file=chunks_file,
            invoices_file=invoices_file,
            table_count=table_count,
            column_count=column_count,
            relationship_count=relationship_count,
            document_chunk_count=chunk_count,
            invoice_count=invoice_count,
            warnings=warnings,
        )

    def load(self, workspace_id: str) -> WorkspaceMetadata:
        path = self._metadata_path(workspace_id)
        if not path.is_file():
            raise WorkspaceNotFoundError("Workspace was not found or has expired.")
        data = json.loads(path.read_text(encoding="utf-8"))
        metadata = WorkspaceMetadata(**data)
        if datetime.fromisoformat(metadata.expires_at) < datetime.now(UTC):
            self.delete(workspace_id)
            raise WorkspaceNotFoundError("Workspace has expired. Upload the source again.")
        return metadata

    def delete(self, workspace_id: str) -> None:
        directory = self._dir(workspace_id)
        if directory.exists():
            shutil.rmtree(directory)

    def resolve_database(self, metadata: WorkspaceMetadata) -> Path:
        if not metadata.database_file:
            raise WorkspaceNotFoundError("This workspace does not contain structured data.")
        return self._dir(metadata.workspace_id) / metadata.database_file

    def resolve_chunks(self, metadata: WorkspaceMetadata) -> Path:
        if not metadata.chunks_file:
            raise WorkspaceNotFoundError("This workspace does not contain document evidence.")
        return self._dir(metadata.workspace_id) / metadata.chunks_file

    def resolve_invoices(self, metadata: WorkspaceMetadata) -> Path:
        if not metadata.invoices_file:
            raise WorkspaceNotFoundError("This workspace does not contain invoice records.")
        return self._dir(metadata.workspace_id) / metadata.invoices_file

    @staticmethod
    def to_info(metadata: WorkspaceMetadata) -> WorkspaceInfo:
        return WorkspaceInfo(
            workspace_id=metadata.workspace_id,
            kind=metadata.kind,
            display_name=metadata.display_name,
            source_files=metadata.source_files,
            created_at=metadata.created_at,
            expires_at=metadata.expires_at,
            database_available=metadata.database_file is not None,
            document_available=metadata.chunks_file is not None,
            table_count=metadata.table_count,
            column_count=metadata.column_count,
            relationship_count=metadata.relationship_count,
            document_chunk_count=metadata.document_chunk_count,
            invoice_count=metadata.invoice_count,
            warnings=metadata.warnings or [],
        )
