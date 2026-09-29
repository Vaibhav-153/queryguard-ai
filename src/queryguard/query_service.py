"""Governed Text-to-SQL orchestration."""

from __future__ import annotations

import time
from pathlib import Path

from queryguard.config import Settings
from queryguard.database import (
    DatabaseError,
    TableSchema,
    allowed_table_names,
    execute_read_only,
    extract_schema,
)
from queryguard.llm import build_text_llm, generate_sql, repair_sql
from queryguard.models import QueryResponse, RetrievedTable, ValidationInfo
from queryguard.retrieval import LexicalSchemaRetriever, RetrievalResult
from queryguard.sql_guard import SQLValidationResult, validate_sql


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 3)


def _schema_context(schema: list[TableSchema], retrieved: list[RetrievalResult]) -> str:
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
    chosen = [table for table in schema if table.name.lower() in expanded] or schema
    return "\n".join(table.as_prompt_text() for table in chosen)


def _validation_info(result: SQLValidationResult) -> ValidationInfo:
    return ValidationInfo(is_safe=result.is_safe, tables=result.tables, warnings=result.warnings)


def _security_rejection(result: SQLValidationResult) -> bool:
    markers = ("Denied SQL operation", "Only read-only SELECT-style", "Exactly one SQL statement")
    return any(any(marker in error for marker in markers) for error in result.errors)


def _clarification(question: str) -> str | None:
    lowered = question.lower()
    vague_rank = any(word in lowered for word in ("best", "top", "worst"))
    metric = any(word in lowered for word in ("revenue", "sales", "count", "price", "total", "average"))
    if vague_rank and not metric:
        return "What metric should be used for the ranking (for example revenue, count, or average value)?"
    return None


def _explain(columns: list[str], rows: list[list[object]], truncated: bool) -> str:
    if not rows:
        return "The query ran successfully and returned no rows."
    message = f"The query returned {len(rows)} row{'s' if len(rows) != 1 else ''}."
    if columns:
        message += " Columns: " + ", ".join(columns) + "."
    if truncated:
        message += " The displayed result reached the configured row limit."
    return message


def _chart(columns: list[str], rows: list[list[object]]) -> str:
    if len(columns) >= 2 and rows:
        numeric = all(isinstance(row[1], (int, float)) for row in rows if len(row) > 1)
        if numeric:
            return "bar"
    return "table" if rows else "none"


class QueryService:
    def __init__(self, settings: Settings, database_path: Path | None = None) -> None:
        self.settings = settings
        self.database_path = database_path or settings.database_path
        self.schema = extract_schema(self.database_path)
        self.retriever = LexicalSchemaRetriever(self.schema)
        self.llm = build_text_llm(settings)
        self.allowed_tables = allowed_table_names(self.schema)

    def ask(self, question: str, top_k_tables: int | None = None) -> QueryResponse:
        started = time.perf_counter()
        timings: dict[str, float] = {}
        question = question.strip()
        clarification = _clarification(question)
        if clarification:
            return QueryResponse(
                status="clarification",
                question=question,
                clarification=clarification,
                latency_ms={"total": _ms(started)},
            )

        retrieval_started = time.perf_counter()
        retrieved = self.retriever.search(question, top_k_tables or self.settings.top_k_tables)
        timings["retrieval"] = _ms(retrieval_started)
        context = _schema_context(self.schema, retrieved)
        retrieved_models = [
            RetrievedTable(table=item.table, score=item.score, reason=item.reason)
            for item in retrieved
        ]

        generation_started = time.perf_counter()
        try:
            sql = generate_sql(self.llm, question, context)
        except Exception as exc:
            return QueryResponse(
                status="error",
                question=question,
                error=f"SQL generation failed: {exc}",
                retrieved_tables=retrieved_models,
                latency_ms={**timings, "generation": _ms(generation_started), "total": _ms(started)},
            )
        timings["generation"] = _ms(generation_started)

        validation_started = time.perf_counter()
        validation = validate_sql(sql, self.allowed_tables)
        timings["validation"] = _ms(validation_started)
        repaired = False

        if not validation.is_safe and not _security_rejection(validation) and self.settings.enable_repair:
            repair_started = time.perf_counter()
            try:
                candidate = repair_sql(self.llm, question, context, sql, "; ".join(validation.errors))
                candidate_validation = validate_sql(candidate, self.allowed_tables)
                if candidate_validation.is_safe:
                    sql, validation, repaired = candidate, candidate_validation, True
            except Exception:
                pass
            timings["repair"] = _ms(repair_started)

        if not validation.is_safe:
            return QueryResponse(
                status="blocked" if _security_rejection(validation) else "error",
                question=question,
                sql=sql,
                error="; ".join(validation.errors),
                validation=_validation_info(validation),
                retrieved_tables=retrieved_models,
                repaired=repaired,
                latency_ms={**timings, "total": _ms(started)},
            )

        execution_started = time.perf_counter()
        try:
            result = execute_read_only(
                self.database_path,
                sql,
                max_rows=self.settings.max_result_rows,
                timeout_ms=self.settings.query_timeout_ms,
            )
        except DatabaseError as exc:
            timings["execution"] = _ms(execution_started)
            if self.settings.enable_repair and not repaired:
                repair_started = time.perf_counter()
                try:
                    candidate = repair_sql(self.llm, question, context, sql, str(exc))
                    candidate_validation = validate_sql(candidate, self.allowed_tables)
                    if candidate_validation.is_safe:
                        second = execute_read_only(
                            self.database_path,
                            candidate,
                            max_rows=self.settings.max_result_rows,
                            timeout_ms=self.settings.query_timeout_ms,
                        )
                        sql, validation, result, repaired = candidate, candidate_validation, second, True
                        timings["repair"] = _ms(repair_started)
                    else:
                        raise DatabaseError("Repaired SQL did not pass validation.")
                except Exception as repair_exc:
                    return QueryResponse(
                        status="error",
                        question=question,
                        sql=sql,
                        error=f"Query execution failed: {exc}; repair failed: {repair_exc}",
                        validation=_validation_info(validation),
                        retrieved_tables=retrieved_models,
                        latency_ms={**timings, "total": _ms(started)},
                    )
            else:
                return QueryResponse(
                    status="error",
                    question=question,
                    sql=sql,
                    error=f"Query execution failed: {exc}",
                    validation=_validation_info(validation),
                    retrieved_tables=retrieved_models,
                    latency_ms={**timings, "total": _ms(started)},
                )

        timings["execution"] = result.execution_ms
        timings["total"] = _ms(started)
        return QueryResponse(
            status="success",
            question=question,
            sql=sql,
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            truncated=result.truncated,
            explanation=_explain(result.columns, result.rows, result.truncated),
            chart_type=_chart(result.columns, result.rows),
            validation=_validation_info(validation),
            retrieved_tables=retrieved_models,
            latency_ms=timings,
            repaired=repaired,
        )
