"""Streamlit interface for QueryGuard AI."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from api_client import APIClientError, QueryGuardAPI
from queryguard.exports import (
    dataframe_to_csv_bytes,
    dataframe_to_xlsx_bytes,
    document_answer_docx_bytes,
    document_answer_markdown,
)
from queryguard.models import DocumentQueryResponse


def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        secret = st.secrets.get(name, default)
    except FileNotFoundError:
        return default
    return str(secret) if secret is not None else default


API_URL = _setting("QUERYGUARD_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = _setting("QUERYGUARD_API_ACCESS_KEY", "")
API = QueryGuardAPI(API_URL, API_KEY)

st.set_page_config(page_title="QueryGuard AI", page_icon="🛡️", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem; padding-bottom: 3rem;}
      [data-testid="stMetricValue"] {font-size: 1.35rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def workspace_key(mode: str) -> str:
    return f"workspace::{mode}"


def show_status() -> dict | None:
    health = API.health()
    with st.sidebar:
        st.title("QueryGuard AI")
        st.caption("Governed Text-to-SQL and evidence-grounded analysis")
        if health:
            st.success("Backend connected")
            st.write(f"**Provider:** {health.get('llm_provider', 'unknown')}")
            st.write(f"**Model:** {health.get('llm_model', 'unknown')}")
            st.write("**SQL validation:** SQLGlot + read-only SQLite")
            st.caption(
                f"Upload limit: {health.get('max_upload_mb', '?')} MB/file · "
                f"{health.get('max_upload_files', '?')} files"
            )
        else:
            st.error("Backend is not reachable")
            st.caption("Check QUERYGUARD_API_URL or wait for a sleeping backend to start.")
        st.divider()
        st.caption("Use public or non-sensitive files on a public deployment.")
    return health


def render_query_response(data: dict, prefix: str) -> None:
    status = data.get("status")
    if status == "clarification":
        st.warning(data.get("clarification", "Please clarify the question."))
        return
    if status == "blocked":
        st.error("The generated SQL was blocked by the safety policy.")
    elif status == "error":
        st.error(data.get("error", "The request failed."))
    else:
        st.success("Query executed through the read-only pipeline.")

    if data.get("sql"):
        st.subheader("Generated SQL")
        st.code(data["sql"], language="sql")

    validation = data.get("validation") or {}
    if validation:
        cols = st.columns(3)
        cols[0].metric("Read-only policy", "Passed" if validation.get("is_safe") else "Blocked")
        cols[1].metric("Tables used", len(validation.get("tables", [])))
        cols[2].metric("Repair used", "Yes" if data.get("repaired") else "No")

    rows = data.get("rows") or []
    columns = data.get("columns") or []
    if rows and columns:
        frame = pd.DataFrame(rows, columns=columns)
        st.subheader("Verified result")
        if data.get("chart_type") == "bar" and len(columns) >= 2:
            try:
                st.bar_chart(frame.set_index(columns[0])[columns[1]])
            except Exception:
                pass
        st.dataframe(frame, use_container_width=True, hide_index=True)
        left, right = st.columns(2)
        left.download_button(
            "Download CSV",
            dataframe_to_csv_bytes(frame),
            file_name=f"{prefix}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        right.download_button(
            "Download Excel",
            dataframe_to_xlsx_bytes(frame),
            file_name=f"{prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if data.get("explanation"):
        st.info(data["explanation"])
    retrieved = data.get("retrieved_tables") or []
    if retrieved:
        with st.expander("Schema retrieval evidence"):
            st.dataframe(pd.DataFrame(retrieved), hide_index=True, use_container_width=True)
    if data.get("latency_ms"):
        with st.expander("Latency"):
            st.json(data["latency_ms"])


def uploader(mode: str, api_mode: str, extensions: list[str], multiple: bool) -> dict | None:
    key = workspace_key(mode)
    workspace = st.session_state.get(key)
    if workspace:
        st.success(f"Active source: {workspace['display_name']}")
        metrics = st.columns(4)
        metrics[0].metric("Tables", workspace.get("table_count", 0))
        metrics[1].metric("Columns", workspace.get("column_count", 0))
        metrics[2].metric("Evidence chunks", workspace.get("document_chunk_count", 0))
        metrics[3].metric("Invoices", workspace.get("invoice_count", 0))
        if st.button("Change source", key=f"change-{mode}"):
            try:
                API.delete_workspace(workspace["workspace_id"])
            except APIClientError:
                pass
            st.session_state.pop(key, None)
            st.rerun()
        return workspace

    uploaded = st.file_uploader(
        "Choose file" if not multiple else "Choose one or more files",
        type=extensions,
        accept_multiple_files=multiple,
        key=f"upload-{mode}",
    )
    files = uploaded if isinstance(uploaded, list) else ([uploaded] if uploaded else [])
    if st.button("Create analysis workspace", type="primary", disabled=not files, key=f"create-{mode}"):
        try:
            with st.spinner("Validating and preparing the source..."):
                workspace = API.upload_workspace(api_mode, files)
            st.session_state[key] = workspace
            st.rerun()
        except APIClientError as exc:
            st.error(str(exc))
    return None


def run_structured(workspace: dict, prefix: str, health: dict | None) -> None:
    if health and health.get("llm_provider") == "demo":
        st.info("Demo provider handles the built-in examples and basic uploaded-table previews. Configure Gemini, Groq, or Ollama for free-form SQL generation.")
    with st.expander("Detected schema"):
        try:
            schema = API.workspace_schema(workspace["workspace_id"])
            for table in schema.get("tables", []):
                st.markdown(f"**{table['name']}**")
                st.dataframe(pd.DataFrame(table.get("columns", [])), hide_index=True, use_container_width=True)
        except APIClientError as exc:
            st.error(str(exc))
    question = st.text_input("Ask a question about this data", key=f"q-{prefix}")
    if st.button("Run governed analysis", type="primary", key=f"run-{prefix}"):
        if not question.strip():
            st.warning("Enter a question first.")
            return
        try:
            with st.spinner("Retrieving schema, generating SQL, validating and executing..."):
                data = API.workspace_query(workspace["workspace_id"], question.strip())
            render_query_response(data, f"queryguard_{prefix}")
        except APIClientError as exc:
            st.error(str(exc))


def render_documents(workspace: dict) -> None:
    question = st.text_input("Ask a question about the documents", key="document-question")
    if st.button("Search documents", type="primary"):
        if not question.strip():
            st.warning("Enter a question first.")
            return
        try:
            with st.spinner("Retrieving supporting passages..."):
                data = API.document_query(workspace["workspace_id"], question.strip())
        except APIClientError as exc:
            st.error(str(exc))
            return
        if data.get("status") == "error":
            st.error(data.get("error", "Document query failed."))
            return
        st.subheader("Answer")
        st.write(data.get("answer"))
        sources = data.get("sources") or []
        if sources:
            st.subheader("Evidence")
            for source in sources:
                with st.expander(f"{source['source_name']} — {source['locator']}"):
                    st.write(source["excerpt"])
                    st.caption(f"Retrieval score: {source['score']}")
        model = DocumentQueryResponse.model_validate(data)
        left, right = st.columns(2)
        left.download_button(
            "Download Markdown report",
            document_answer_markdown(model).encode("utf-8"),
            file_name="queryguard_document_answer.md",
            mime="text/markdown",
            use_container_width=True,
        )
        right.download_button(
            "Download Word report",
            document_answer_docx_bytes(model),
            file_name="queryguard_document_answer.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )


health = show_status()
st.title("QueryGuard AI")
st.write(
    "Ask questions over a demo database, uploaded SQLite/Excel/CSV data, documents, or invoices. "
    "SQL is validated before it reaches a read-only SQLite connection."
)

mode = st.radio(
    "Analysis mode",
    ["Demo", "Database", "Spreadsheet", "Documents", "Invoices"],
    horizontal=True,
)

if mode == "Demo":
    st.header("Built-in demo")
    examples = [
        "Show the top 5 customers by revenue",
        "Which countries generated the most revenue?",
        "Which genres have the most tracks?",
        "What is the average track price?",
        "How many customers are in the database?",
    ]
    question = st.selectbox("Example question", examples)
    if st.button("Run demo query", type="primary"):
        try:
            render_query_response(API.demo_query(question), "queryguard_demo")
        except APIClientError as exc:
            st.error(str(exc))
elif mode == "Database":
    st.header("Analyze SQLite data")
    workspace = uploader("database", "database", ["db", "sqlite", "sqlite3"], False)
    if workspace:
        run_structured(workspace, "database", health)
elif mode == "Spreadsheet":
    st.header("Analyze Excel or CSV data")
    workspace = uploader("spreadsheet", "spreadsheet", ["xlsx", "csv"], False)
    if workspace:
        run_structured(workspace, "spreadsheet", health)
elif mode == "Documents":
    st.header("Ask cited questions over documents")
    workspace = uploader("documents", "document", ["pdf", "docx", "pptx"], True)
    if workspace:
        render_documents(workspace)
else:
    st.header("Invoice analysis")
    workspace = uploader("invoices", "invoice", ["pdf", "png", "jpg", "jpeg", "xlsx", "csv"], True)
    if workspace:
        try:
            records = API.invoice_records(workspace["workspace_id"])
            frame = pd.DataFrame(records.get("records", []))
            if not frame.empty:
                st.subheader("Extracted invoice fields")
                st.dataframe(frame, hide_index=True, use_container_width=True)
                st.download_button(
                    "Download invoice CSV",
                    dataframe_to_csv_bytes(frame),
                    file_name="queryguard_invoices.csv",
                    mime="text/csv",
                )
        except APIClientError as exc:
            st.error(str(exc))
        if workspace.get("database_available"):
            run_structured(workspace, "invoice", health)
        if workspace.get("document_available"):
            st.subheader("Ask about invoice text")
            render_documents(workspace)
