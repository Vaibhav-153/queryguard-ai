"""FastAPI entry point."""

from __future__ import annotations

import hmac
import os

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader

from queryguard import __version__
from queryguard.config import Settings, get_settings
from queryguard.database.schema import extract_schema
from queryguard.logging_config import configure_logging
from queryguard.models import HealthResponse, QueryRequest, QueryResponse
from queryguard.services.query_service import QueryService

QUERY_KEY_HEADER = "X-QueryGuard-Key"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Governed natural-language to SQL analytics API. "
            "Hosted deployments can protect query execution with X-QueryGuard-Key."
        ),
    )
    app.state.settings = settings
    app.state.query_service = None
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

    def service(request: Request) -> QueryService:
        if request.app.state.query_service is None:
            try:
                request.app.state.query_service = QueryService(request.app.state.settings)
            except ValueError as exc:
                raise HTTPException(
                    status_code=503,
                    detail=f"LLM provider configuration error: {exc}",
                ) from exc
        return request.app.state.query_service

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
        )

    @app.get("/schema")
    def schema(request: Request) -> dict:
        try:
            tables = extract_schema(request.app.state.settings.database_path)
        except Exception as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
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

    @app.post(
        "/query",
        response_model=QueryResponse,
        dependencies=[Depends(require_query_key)],
    )
    def query(payload: QueryRequest, request: Request) -> QueryResponse:
        return service(request).ask(payload.question, payload.top_k_tables)

    return app


app = create_app()


def run() -> None:
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("queryguard.api.main:app", host="0.0.0.0", port=port, reload=False)
