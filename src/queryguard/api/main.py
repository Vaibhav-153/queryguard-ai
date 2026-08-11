"""FastAPI entry point for demo and uploaded-workspace analysis."""

from __future__ import annotations

import hmac
import os
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Security, UploadFile
from fastapi.security import APIKeyHeader

from queryguard import __version__
from queryguard.config import Settings, get_settings
from queryguard.database.schema import TableSchema, extract_schema
from queryguard.documents.storage import load_chunks
from queryguard.ingestion.common import IngestionError
from queryguard.ingestion.ocr import ocr_available
from queryguard.invoices.storage import load_invoice_records
from queryguard.logging_config import configure_logging
from queryguard.models import (
    DocumentQueryRequest,
    DocumentQueryResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    WorkspaceInfo,
)
from queryguard.services.document_service import DocumentService
from queryguard.services.query_service import QueryService
from queryguard.workspaces.manager import (
    UploadContent,
    WorkspaceManager,
    WorkspaceNotFoundError,
)

QUERY_KEY_HEADER = "X-QueryGuard-Key"
SUPPORTED_SOURCES = [
    "Chinook demo",
    "SQLite (.db/.sqlite/.sqlite3)",
    "Excel (.xlsx)",
    "CSV (.csv)",
    "PDF (.pdf)",
    "Word (.docx)",
    "PowerPoint (.pptx)",
    "Invoices (.pdf/.png/.jpg/.jpeg/.xlsx/.csv)",
]


def _schema_payload(tables: list[TableSchema]) -> dict:
    return {
        "tables": [
            {
                "name": table.name,
                "columns": [
                    {
                        "name": column.name,
                        "type": column.data_type,
                        "nullable": column.nullable,
                        "primary_key": column.primary_key,
                    }
                    for column in table.columns
                ],
                "foreign_keys": [
                    {
                        "from": fk.from_column,
                        "target_table": fk.target_table,
                        "target_column": fk.target_column,
                    }
                    for fk in table.foreign_keys
                ],
            }
            for table in tables
        ]
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Governed data and document intelligence API with Text-to-SQL, "
            "document retrieval, invoice normalization, and isolated uploads."
        ),
    )
    app.state.settings = settings
    app.state.demo_query_service = None
    app.state.workspace_manager = WorkspaceManager(settings)

    api_key_header = APIKeyHeader(name=QUERY_KEY_HEADER, auto_error=False)

    def require_query_key(provided_key: str | None = Security(api_key_header)) -> None:
        expected = settings.api_access_key
        if expected is None or not expected.get_secret_value():
            return
        if not provided_key or not hmac.compare_digest(
            provided_key,
            expected.get_secret_value(),
        ):
            raise HTTPException(status_code=401, detail="Invalid or missing QueryGuard access key.")

    def demo_service(request: Request) -> QueryService:
        if request.app.state.demo_query_service is None:
            try:
                request.app.state.demo_query_service = QueryService(request.app.state.settings)
            except ValueError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"LLM provider configuration error: {exc}",
                ) from exc
        return request.app.state.demo_query_service

    def manager(request: Request) -> WorkspaceManager:
        return request.app.state.workspace_manager

    @app.get("/health", response_model=HealthResponse)
    def health(request: Request) -> HealthResponse:
        current: Settings = request.app.state.settings
        return HealthResponse(
            status="ok" if current.database_path.is_file() else "degraded",
            app=current.app_name,
            version=__version__,
            database_available=current.database_path.is_file(),
            llm_provider=current.llm_provider,
            llm_model=current.llm_model_name,
            retrieval_strategy=current.retrieval_strategy,
            api_protected=bool(
                current.api_access_key and current.api_access_key.get_secret_value()
            ),
            max_upload_mb=current.max_upload_mb,
            max_total_upload_mb=current.max_total_upload_mb,
            max_upload_files=current.max_upload_files,
            workspace_ttl_minutes=current.workspace_ttl_minutes,
            ocr_available=ocr_available(),
            supported_sources=SUPPORTED_SOURCES,
        )

    @app.get("/schema")
    def demo_schema(request: Request) -> dict:
        try:
            tables = extract_schema(request.app.state.settings.database_path)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return _schema_payload(tables)

    @app.post(
        "/query",
        response_model=QueryResponse,
        dependencies=[Depends(require_query_key)],
    )
    def demo_query(payload: QueryRequest, request: Request) -> QueryResponse:
        return demo_service(request).ask(payload.question, payload.top_k_tables)

    @app.post(
        "/workspaces/upload",
        response_model=WorkspaceInfo,
        dependencies=[Depends(require_query_key)],
    )
    async def upload_workspace(
        request: Request,
        mode: Annotated[str, Form()],
        files: Annotated[list[UploadFile], File()],
    ) -> WorkspaceInfo:
        current: Settings = request.app.state.settings
        if len(files) > current.max_upload_files:
            raise HTTPException(
                status_code=413,
                detail=f"At most {current.max_upload_files} files can be uploaded at once.",
            )

        uploads: list[UploadContent] = []
        total_bytes = 0
        for file in files:
            content = await file.read(current.max_upload_bytes + 1)
            if len(content) > current.max_upload_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"{file.filename or 'upload'} exceeds the {current.max_upload_mb} MB limit.",
                )
            total_bytes += len(content)
            if total_bytes > current.max_total_upload_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "The combined upload exceeds the "
                        f"{current.max_total_upload_mb} MB workspace limit."
                    ),
                )
            uploads.append(
                UploadContent(
                    name=file.filename or "upload.bin",
                    content=content,
                )
            )

        try:
            return manager(request).create(mode, uploads)
        except IngestionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(
        "/workspaces/{workspace_id}",
        response_model=WorkspaceInfo,
        dependencies=[Depends(require_query_key)],
    )
    def workspace_info(workspace_id: str, request: Request) -> WorkspaceInfo:
        try:
            metadata = manager(request).load(workspace_id)
            return manager(request).to_info(metadata)
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete(
        "/workspaces/{workspace_id}",
        dependencies=[Depends(require_query_key)],
    )
    def delete_workspace(workspace_id: str, request: Request) -> dict[str, str]:
        manager(request).delete(workspace_id)
        return {"status": "deleted", "workspace_id": workspace_id}

    @app.get(
        "/workspaces/{workspace_id}/schema",
        dependencies=[Depends(require_query_key)],
    )
    def workspace_schema(workspace_id: str, request: Request) -> dict:
        try:
            workspace_manager = manager(request)
            metadata = workspace_manager.load(workspace_id)
            database_path = workspace_manager.resolve_database(metadata)
            return _schema_payload(extract_schema(database_path))
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/workspaces/{workspace_id}/query",
        response_model=QueryResponse,
        dependencies=[Depends(require_query_key)],
    )
    def workspace_query(
        workspace_id: str,
        payload: QueryRequest,
        request: Request,
    ) -> QueryResponse:
        try:
            workspace_manager = manager(request)
            metadata = workspace_manager.load(workspace_id)
            database_path = workspace_manager.resolve_database(metadata)
            service = QueryService(request.app.state.settings, database_path=database_path)
            return service.ask(payload.question, payload.top_k_tables)
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/workspaces/{workspace_id}/document-query",
        response_model=DocumentQueryResponse,
        dependencies=[Depends(require_query_key)],
    )
    def workspace_document_query(
        workspace_id: str,
        payload: DocumentQueryRequest,
        request: Request,
    ) -> DocumentQueryResponse:
        try:
            workspace_manager = manager(request)
            metadata = workspace_manager.load(workspace_id)
            chunks = load_chunks(workspace_manager.resolve_chunks(metadata))
            service = DocumentService(request.app.state.settings, chunks)
            return service.ask(payload.question, payload.top_k)
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get(
        "/workspaces/{workspace_id}/invoice-records",
        dependencies=[Depends(require_query_key)],
    )
    def invoice_records(workspace_id: str, request: Request) -> dict:
        try:
            workspace_manager = manager(request)
            metadata = workspace_manager.load(workspace_id)
            records = load_invoice_records(workspace_manager.resolve_invoices(metadata))
            public_records = [record.model_dump(exclude={"raw_text"}) for record in records]
            return {"records": public_records, "count": len(public_records)}
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()


def run() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("queryguard.api.main:app", host="0.0.0.0", port=port, reload=False)
