"""End-to-end governed text-to-SQL request service."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from queryguard.analysis.ambiguity import detect_ambiguity
from queryguard.analysis.presentation import choose_chart, explain_result
from queryguard.config import Settings
from queryguard.database.connection import DatabaseError, execute_read_only
from queryguard.database.schema import TableSchema, allowed_table_names, extract_schema
from queryguard.governance.validator import SQLValidationResult, validate_sql
from queryguard.llm.base import SQLGenerator
from queryguard.llm.factory import build_sql_generator
from queryguard.models import QueryResponse, RetrievedTable, ValidationInfo
from queryguard.retrieval.base import RetrievalResult, SchemaRetriever
from queryguard.retrieval.factory import build_retriever

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineDependencies:
    schema: list[TableSchema]
    retriever: SchemaRetriever
    generator: SQLGenerator


def _milliseconds(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def _schema_context(schema: list[TableSchema], retrieved: list[RetrievalResult]) -> str:
    """Include selected tables plus one-hop foreign-key neighbours."""
    selected = {item.table.lower() for item in retrieved}
    table_by_name = {table.name.lower(): table for table in schema}

    expanded = set(selected)
    for name in list(selected):
        table = table_by_name.get(name)
        if table:
            expanded.update(fk.target_table.lower() for fk in table.foreign_keys)
        for candidate in schema:
            if any(fk.target_table.lower() == name for fk in candidate.foreign_keys):
                expanded.add(candidate.name.lower())

    chosen = [table for table in schema if table.name.lower() in expanded]
    if not chosen:
        chosen = schema
    return "\n".join(table.as_prompt_text() for table in chosen)


def _validation_model(result: SQLValidationResult) -> ValidationInfo:
    return ValidationInfo(
        is_safe=result.is_safe,
        tables=result.tables,
        warnings=result.warnings,
    )


def _is_security_rejection(validation: SQLValidationResult) -> bool:
    security_markers = (
        "Denied SQL operation",
        "Only read-only SELECT-style",
        "Exactly one SQL statement",
    )
    return any(any(marker in error for marker in security_markers) for error in validation.errors)


class QueryService:
    def __init__(
        self,
        settings: Settings,
        dependencies: PipelineDependencies | None = None,
    ) -> None:
        self.settings = settings
        if dependencies is None:
            schema = extract_schema(settings.database_path)
            dependencies = PipelineDependencies(
                schema=schema,
                retriever=build_retriever(settings, schema),
                generator=build_sql_generator(settings),
            )
        self.schema = dependencies.schema
        self.retriever = dependencies.retriever
        self.generator = dependencies.generator
        self.allowed_tables = allowed_table_names(self.schema)

    def ask(self, question: str, top_k_tables: int | None = None) -> QueryResponse:
        request_start = time.perf_counter()
        timings: dict[str, float] = {}
        question = question.strip()

        ambiguity = detect_ambiguity(question)
        if ambiguity.ambiguous:
            return QueryResponse(
                status="clarification",
                question=question,
                clarification=ambiguity.clarification,
                error=ambiguity.reason,
                latency_ms={"total": _milliseconds(request_start)},
            )

        retrieval_start = time.perf_counter()
        top_k = top_k_tables or self.settings.top_k_tables
        retrieved = self.retriever.search(question, top_k)
        timings["retrieval"] = _milliseconds(retrieval_start)
        context = _schema_context(self.schema, retrieved)
        retrieved_models = [
            RetrievedTable(table=item.table, score=item.score, reason=item.reason)
            for item in retrieved
        ]

        generation_start = time.perf_counter()
        try:
            sql = self.generator.generate_sql(question, context).strip().rstrip(";")
        except Exception as exc:  # Converted to a controlled API error below.
            LOGGER.exception("SQL generation failed")
            return QueryResponse(
                status="error",
                question=question,
                error=f"SQL generation failed: {exc}",
                retrieved_tables=retrieved_models,
                latency_ms={**timings, "generation": _milliseconds(generation_start), "total": _milliseconds(request_start)},
            )
        timings["generation"] = _milliseconds(generation_start)

        validation_start = time.perf_counter()
        validation = validate_sql(sql, self.allowed_tables)
        timings["validation"] = _milliseconds(validation_start)
        repaired = False

        if not validation.is_safe:
            if _is_security_rejection(validation):
                return QueryResponse(
                    status="blocked",
                    question=question,
                    sql=sql,
                    error="; ".join(validation.errors),
                    validation=_validation_model(validation),
                    retrieved_tables=retrieved_models,
                    latency_ms={**timings, "total": _milliseconds(request_start)},
                )
            if self.settings.enable_repair:
                repaired_response = self._repair_once(
                    question=question,
                    context=context,
                    previous_sql=sql,
                    failure="; ".join(validation.errors),
                )
                if repaired_response is not None:
                    sql, validation, repair_ms = repaired_response
                    timings["repair"] = repair_ms
                    repaired = True
            if not validation.is_safe:
                return QueryResponse(
                    status="error",
                    question=question,
                    sql=sql,
                    error="; ".join(validation.errors),
                    validation=_validation_model(validation),
                    retrieved_tables=retrieved_models,
                    repaired=repaired,
                    latency_ms={**timings, "total": _milliseconds(request_start)},
                )

        execution_start = time.perf_counter()
        try:
            result = execute_read_only(
                self.settings.database_path,
                sql,
                max_rows=self.settings.max_result_rows,
                timeout_ms=self.settings.query_timeout_ms,
            )
            timings["execution"] = result.execution_ms
        except DatabaseError as exc:
            timings["execution"] = _milliseconds(execution_start)
            if self.settings.enable_repair and not repaired:
                repaired_response = self._repair_once(
                    question=question,
                    context=context,
                    previous_sql=sql,
                    failure=str(exc),
                )
                if repaired_response is not None:
                    repaired_sql, repaired_validation, repair_ms = repaired_response
                    timings["repair"] = repair_ms
                    repaired = True
                    if repaired_validation.is_safe:
                        try:
                            result = execute_read_only(
                                self.settings.database_path,
                                repaired_sql,
                                max_rows=self.settings.max_result_rows,
                                timeout_ms=self.settings.query_timeout_ms,
                            )
                            sql = repaired_sql
                            validation = repaired_validation
                            timings["execution"] = result.execution_ms
                        except DatabaseError as second_exc:
                            return self._execution_error_response(
                                question,
                                repaired_sql,
                                repaired_validation,
                                retrieved_models,
                                timings,
                                request_start,
                                repaired,
                                str(second_exc),
                            )
                    else:
                        return self._execution_error_response(
                            question,
                            repaired_sql,
                            repaired_validation,
                            retrieved_models,
                            timings,
                            request_start,
                            repaired,
                            "; ".join(repaired_validation.errors),
                        )
                else:
                    return self._execution_error_response(
                        question, sql, validation, retrieved_models, timings, request_start, repaired, str(exc)
                    )
            else:
                return self._execution_error_response(
                    question, sql, validation, retrieved_models, timings, request_start, repaired, str(exc)
                )

        timings["total"] = _milliseconds(request_start)
        LOGGER.info(
            "query_success tables=%s rows=%s repaired=%s total_ms=%s",
            validation.tables,
            result.row_count,
            repaired,
            timings["total"],
        )
        return QueryResponse(
            status="success",
            question=question,
            sql=sql,
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            truncated=result.truncated,
            explanation=explain_result(result.columns, result.rows, result.truncated),
            chart_type=choose_chart(result.columns, result.rows),
            validation=_validation_model(validation),
            retrieved_tables=retrieved_models,
            latency_ms=timings,
            repaired=repaired,
        )

    def _repair_once(
        self,
        question: str,
        context: str,
        previous_sql: str,
        failure: str,
    ) -> tuple[str, SQLValidationResult, float] | None:
        start = time.perf_counter()
        try:
            repaired_sql = self.generator.repair_sql(
                question,
                context,
                previous_sql,
                failure,
            ).strip().rstrip(";")
        except Exception:
            LOGGER.exception("SQL repair failed")
            return None
        validation = validate_sql(repaired_sql, self.allowed_tables)
        return repaired_sql, validation, _milliseconds(start)

    @staticmethod
    def _execution_error_response(
        question: str,
        sql: str,
        validation: SQLValidationResult,
        retrieved: list[RetrievedTable],
        timings: dict[str, float],
        request_start: float,
        repaired: bool,
        error: str,
    ) -> QueryResponse:
        timings = {**timings, "total": _milliseconds(request_start)}
        return QueryResponse(
            status="error",
            question=question,
            sql=sql,
            error=error,
            validation=_validation_model(validation),
            retrieved_tables=retrieved,
            repaired=repaired,
            latency_ms=timings,
        )
