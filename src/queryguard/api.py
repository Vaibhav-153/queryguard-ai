"""FastAPI entry point for demo and uploaded-workspace analysis."""

from __future__ import annotations

import hmac
import os

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Security, UploadFile
from fastapi.security import APIKeyHeader

from queryguard import __version__
from queryguard.config import Settings, get_settings
from queryguard.database import extract_schema
from queryguard.documents import DocumentService, load_chunks
from queryguard.ingestion import IngestionError
from queryguard.invoices import load_invoice_records
from queryguard.models import (
    DocumentQueryRequest,
    DocumentQueryResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    WorkspaceInfo,
)
from queryguard.query_service import QueryService
from queryguard.workspaces import UploadContent, WorkspaceManager, WorkspaceNotFoundError

SUPPORTED_SOURCES = [
    "Bundled SQLite demo",
    "SQLite (.db/.sqlite/.sqlite3)",
    "Excel (.xlsx)",
    "CSV (.csv)",
    "PDF (.pdf)",
    "Word (.docx)",
    "PowerPoint (.pptx)",
    "Invoices (.pdf/.png/.jpg/.jpeg/.xlsx/.csv)",
]


def _ocr_available() -> bool:
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return True


def _schema_payload(database_path) -> dict:
    tables = extract_schema(database_path)
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
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="Governed Text-to-SQL, document Q&A, and invoice analytics API.",
    )
    app.state.settings = settings
    app.state.demo_query_service = None
    app.state.workspace_manager = WorkspaceManager(settings)

    header = APIKeyHeader(name="X-QueryGuard-Key", auto_error=False)

    def require_key(provided: str | None = Security(header)) -> None:
        expected = settings.api_access_key
        if expected is None or not expected.get_secret_value():
            return
        if not provided or not hmac.compare_digest(provided, expected.get_secret_value()):
            raise HTTPException(status_code=401, detail="Invalid or missing QueryGuard access key.")

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
            api_protected=bool(current.api_access_key and current.api_access_key.get_secret_value()),
            max_upload_mb=current.max_upload_mb,
            max_total_upload_mb=current.max_total_upload_mb,
            max_upload_files=current.max_upload_files,
            workspace_ttl_minutes=current.workspace_ttl_minutes,
            ocr_available=_ocr_available(),
            supported_sources=SUPPORTED_SOURCES,
        )

    @app.get("/schema")
    def demo_schema(request: Request) -> dict:
        try:
            return _schema_payload(request.app.state.settings.database_path)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/query", response_model=QueryResponse, dependencies=[Depends(require_key)])
    def demo_query(payload: QueryRequest, request: Request) -> QueryResponse:
        if request.app.state.demo_query_service is None:
            try:
                request.app.state.demo_query_service = QueryService(request.app.state.settings)
            except Exception as exc:
                raise HTTPException(status_code=503, detail=str(exc)) from exc
        return request.app.state.demo_query_service.ask(payload.question, payload.top_k_tables)

    @app.post("/workspaces/upload", response_model=WorkspaceInfo, dependencies=[Depends(require_key)])
    async def upload_workspace(
        request: Request,
        mode: str = Form(...),
        files: list[UploadFile] = File(...),
    ) -> WorkspaceInfo:
        current: Settings = request.app.state.settings
        if len(files) > current.max_upload_files:
            raise HTTPException(status_code=413, detail="Too many files in one upload.")
        uploads: list[UploadContent] = []
        total = 0
        for file in files:
            content = await file.read(current.max_upload_bytes + 1)
            if len(content) > current.max_upload_bytes:
                raise HTTPException(status_code=413, detail=f"{file.filename or 'upload'} is too large.")
            total += len(content)
            if total > current.max_total_upload_bytes:
                raise HTTPException(status_code=413, detail="Combined upload is too large.")
            uploads.append(UploadContent(file.filename or "upload.bin", content))
        try:
            return manager(request).create(mode, uploads)
        except IngestionError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/workspaces/{workspace_id}", response_model=WorkspaceInfo, dependencies=[Depends(require_key)])
    def workspace_info(workspace_id: str, request: Request) -> WorkspaceInfo:
        try:
            metadata = manager(request).load(workspace_id)
            return manager(request).to_info(metadata)
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete("/workspaces/{workspace_id}", dependencies=[Depends(require_key)])
    def delete_workspace(workspace_id: str, request: Request) -> dict[str, str]:
        manager(request).delete(workspace_id)
        return {"status": "deleted", "workspace_id": workspace_id}

    @app.get("/workspaces/{workspace_id}/schema", dependencies=[Depends(require_key)])
    def workspace_schema(workspace_id: str, request: Request) -> dict:
        try:
            metadata = manager(request).load(workspace_id)
            return _schema_payload(manager(request).resolve_database(metadata))
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post("/workspaces/{workspace_id}/query", response_model=QueryResponse, dependencies=[Depends(require_key)])
    def workspace_query(workspace_id: str, payload: QueryRequest, request: Request) -> QueryResponse:
        try:
            metadata = manager(request).load(workspace_id)
            database_path = manager(request).resolve_database(metadata)
            return QueryService(request.app.state.settings, database_path).ask(
                payload.question, payload.top_k_tables
            )
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post(
        "/workspaces/{workspace_id}/document-query",
        response_model=DocumentQueryResponse,
        dependencies=[Depends(require_key)],
    )
    def workspace_document_query(
        workspace_id: str, payload: DocumentQueryRequest, request: Request
    ) -> DocumentQueryResponse:
        try:
            metadata = manager(request).load(workspace_id)
            chunks = load_chunks(manager(request).resolve_chunks(metadata))
            return DocumentService(request.app.state.settings, chunks).ask(payload.question, payload.top_k)
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/workspaces/{workspace_id}/invoice-records", dependencies=[Depends(require_key)])
    def invoice_records(workspace_id: str, request: Request) -> dict:
        try:
            metadata = manager(request).load(workspace_id)
            records = load_invoice_records(manager(request).resolve_invoices(metadata))
            public = [
                {
                    "source_name": r.source_name,
                    "invoice_number": r.invoice_number,
                    "invoice_date": r.invoice_date,
                    "vendor": r.vendor,
                    "customer": r.customer,
                    "currency": r.currency,
                    "total": r.total,
                    "needs_review": r.needs_review,
                }
                for r in records
            ]
            return {"records": public, "count": len(public)}
        except WorkspaceNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return app


app = create_app()


def run() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("queryguard.api:app", host="0.0.0.0", port=port, reload=False)
