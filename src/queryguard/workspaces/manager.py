"""Create and manage isolated personal-analysis workspaces."""

from __future__ import annotations

import shutil
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from queryguard.config import Settings
from queryguard.database.schema import extract_schema
from queryguard.documents.chunking import chunk_units
from queryguard.documents.storage import save_chunks
from queryguard.ingestion.common import IngestionError, safe_filename
from queryguard.ingestion.document_loader import DOCUMENT_EXTENSIONS, extract_document_units
from queryguard.ingestion.spreadsheet_loader import SPREADSHEET_EXTENSIONS, spreadsheet_to_sqlite
from queryguard.ingestion.sqlite_loader import SQLITE_EXTENSIONS, validate_sqlite_database
from queryguard.invoices.database import write_invoice_database
from queryguard.invoices.parser import INVOICE_EXTENSIONS, parse_invoice_file
from queryguard.invoices.storage import save_invoice_records
from queryguard.models import WorkspaceInfo
from queryguard.workspaces.models import WorkspaceMetadata


@dataclass(frozen=True, slots=True)
class UploadContent:
    name: str
    content: bytes


class WorkspaceNotFoundError(RuntimeError):
    pass


class WorkspaceManager:
    """Filesystem-backed workspace manager suitable for local and portfolio use."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.root = settings.workspace_root
        self.root.mkdir(parents=True, exist_ok=True)

    def _workspace_dir(self, workspace_id: str) -> Path:
        if len(workspace_id) != 32 or any(char not in "0123456789abcdef" for char in workspace_id):
            raise WorkspaceNotFoundError("Invalid workspace identifier.")
        return self.root / workspace_id

    @staticmethod
    def _metadata_path(directory: Path) -> Path:
        return directory / "metadata.json"

    def _save_metadata(self, directory: Path, metadata: WorkspaceMetadata) -> None:
        self._metadata_path(directory).write_text(
            metadata.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def load(self, workspace_id: str) -> WorkspaceMetadata:
        directory = self._workspace_dir(workspace_id)
        path = self._metadata_path(directory)
        if not path.is_file():
            raise WorkspaceNotFoundError("Workspace was not found or has expired.")
        metadata = WorkspaceMetadata.model_validate_json(path.read_text(encoding="utf-8"))
        if metadata.expires_at < datetime.now(UTC):
            shutil.rmtree(directory, ignore_errors=True)
            raise WorkspaceNotFoundError("Workspace has expired. Upload the source again.")
        return metadata

    def delete(self, workspace_id: str) -> None:
        directory = self._workspace_dir(workspace_id)
        if directory.exists():
            shutil.rmtree(directory)

    def cleanup_expired(self) -> int:
        removed = 0
        now = datetime.now(UTC)
        for directory in self.root.iterdir():
            if not directory.is_dir():
                continue
            metadata_path = self._metadata_path(directory)
            try:
                metadata = WorkspaceMetadata.model_validate_json(
                    metadata_path.read_text(encoding="utf-8")
                )
            except Exception:
                continue
            if metadata.expires_at < now:
                shutil.rmtree(directory, ignore_errors=True)
                removed += 1
        return removed

    def create(self, kind: str, uploads: list[UploadContent]) -> WorkspaceInfo:
        """Validate uploads and build a workspace-specific analysis index/database."""
        if kind not in {"database", "spreadsheet", "document", "invoice"}:
            raise IngestionError(f"Unsupported workspace kind: {kind}")
        if not uploads:
            raise IngestionError("At least one file is required.")
        if len(uploads) > self.settings.max_upload_files:
            raise IngestionError(
                f"At most {self.settings.max_upload_files} files can be uploaded at once."
            )
        total_bytes = sum(len(upload.content) for upload in uploads)
        if total_bytes > self.settings.max_total_upload_bytes:
            raise IngestionError(
                "The combined upload exceeds the "
                f"{self.settings.max_total_upload_mb} MB workspace limit."
            )
        if kind in {"database", "spreadsheet"} and len(uploads) != 1:
            raise IngestionError(f"{kind.title()} mode accepts one source file at a time.")

        self.cleanup_expired()
        workspace_id = uuid.uuid4().hex
        directory = self.root / workspace_id
        uploads_dir = directory / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=False)

        try:
            stored_paths = self._store_uploads(uploads_dir, uploads)
            metadata = self._build_metadata(workspace_id, kind, directory, stored_paths)
            self._save_metadata(directory, metadata)
            return self.to_info(metadata)
        except Exception:
            shutil.rmtree(directory, ignore_errors=True)
            raise

    def _store_uploads(self, uploads_dir: Path, uploads: list[UploadContent]) -> list[Path]:
        stored: list[Path] = []
        for upload in uploads:
            if len(upload.content) > self.settings.max_upload_bytes:
                raise IngestionError(
                    f"{upload.name} exceeds the {self.settings.max_upload_mb} MB upload limit."
                )
            name = safe_filename(upload.name)
            path = uploads_dir / name
            if path.exists():
                path = uploads_dir / f"{path.stem}_{len(stored) + 1}{path.suffix}"
            path.write_bytes(upload.content)
            stored.append(path)
        return stored

    def _build_metadata(
        self,
        workspace_id: str,
        kind: str,
        directory: Path,
        paths: list[Path],
    ) -> WorkspaceMetadata:
        now = datetime.now(UTC)
        expires = now + timedelta(minutes=self.settings.workspace_ttl_minutes)
        warnings: list[str] = []
        database_file: str | None = None
        chunks_file: str | None = None
        invoices_file: str | None = None
        invoice_count = 0
        document_chunk_count = 0

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
            result = spreadsheet_to_sqlite(
                path,
                database_path,
                max_office_uncompressed_bytes=self.settings.max_office_uncompressed_bytes,
            )
            warnings.extend(result.warnings)
            database_file = str(database_path.relative_to(directory))

        elif kind == "document":
            units = []
            for path in paths:
                if path.suffix.lower() not in DOCUMENT_EXTENSIONS:
                    raise IngestionError("Document mode accepts .pdf, .docx, or .pptx files.")
                parsed, parser_warnings = extract_document_units(
                    path,
                    max_uncompressed_bytes=self.settings.max_office_uncompressed_bytes,
                )
                units.extend(parsed)
                warnings.extend(parser_warnings)
            chunks = chunk_units(units)
            chunks_path = directory / "document_chunks.json"
            save_chunks(chunks, chunks_path)
            chunks_file = str(chunks_path.relative_to(directory))
            document_chunk_count = len(chunks)

        else:
            records = []
            units = []
            for path in paths:
                if path.suffix.lower() not in INVOICE_EXTENSIONS:
                    raise IngestionError(
                        "Invoice mode accepts .pdf, .png, .jpg, .jpeg, .xlsx, or .csv files."
                    )
                parsed_records, parsed_units, parser_warnings = parse_invoice_file(
                    path,
                    max_office_uncompressed_bytes=self.settings.max_office_uncompressed_bytes,
                )
                records.extend(parsed_records)
                units.extend(parsed_units)
                warnings.extend(parser_warnings)

            if not records:
                raise IngestionError("No invoice records could be extracted.")
            database_path = directory / "invoices.sqlite"
            write_invoice_database(records, database_path)
            records_path = directory / "invoice_records.json"
            save_invoice_records(records, records_path)
            database_file = str(database_path.relative_to(directory))
            invoices_file = str(records_path.relative_to(directory))
            invoice_count = len(records)

            if units:
                chunks = chunk_units(units)
                chunks_path = directory / "invoice_chunks.json"
                save_chunks(chunks, chunks_path)
                chunks_file = str(chunks_path.relative_to(directory))
                document_chunk_count = len(chunks)

        table_count = 0
        column_count = 0
        relationship_count = 0
        if database_file:
            database_path = directory / database_file
            schema = extract_schema(database_path)
            table_count = len(schema)
            column_count = sum(len(table.columns) for table in schema)
            relationship_count = sum(len(table.foreign_keys) for table in schema)

        return WorkspaceMetadata(
            workspace_id=workspace_id,
            kind=kind,
            display_name=paths[0].name if len(paths) == 1 else f"{len(paths)} uploaded files",
            source_files=[path.name for path in paths],
            created_at=now,
            expires_at=expires,
            database_file=database_file,
            chunks_file=chunks_file,
            invoices_file=invoices_file,
            table_count=table_count,
            column_count=column_count,
            relationship_count=relationship_count,
            document_chunk_count=document_chunk_count,
            invoice_count=invoice_count,
            warnings=warnings,
        )

    def resolve_database(self, metadata: WorkspaceMetadata) -> Path:
        if not metadata.database_file:
            raise WorkspaceNotFoundError("This workspace does not contain a structured database.")
        return self._workspace_dir(metadata.workspace_id) / metadata.database_file

    def resolve_chunks(self, metadata: WorkspaceMetadata) -> Path:
        if not metadata.chunks_file:
            raise WorkspaceNotFoundError("This workspace does not contain document evidence.")
        return self._workspace_dir(metadata.workspace_id) / metadata.chunks_file

    def resolve_invoices(self, metadata: WorkspaceMetadata) -> Path:
        if not metadata.invoices_file:
            raise WorkspaceNotFoundError("This workspace does not contain invoice records.")
        return self._workspace_dir(metadata.workspace_id) / metadata.invoices_file

    @staticmethod
    def to_info(metadata: WorkspaceMetadata) -> WorkspaceInfo:
        return WorkspaceInfo(
            workspace_id=metadata.workspace_id,
            kind=metadata.kind,
            display_name=metadata.display_name,
            source_files=metadata.source_files,
            created_at=metadata.created_at.isoformat(),
            expires_at=metadata.expires_at.isoformat(),
            database_available=metadata.database_file is not None,
            document_available=metadata.chunks_file is not None,
            table_count=metadata.table_count,
            column_count=metadata.column_count,
            relationship_count=metadata.relationship_count,
            document_chunk_count=metadata.document_chunk_count,
            invoice_count=metadata.invoice_count,
            warnings=metadata.warnings,
        )
