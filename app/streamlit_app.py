"""Recruiter-facing Streamlit interface for QueryGuard AI."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from api_client import APIClientError, QueryGuardAPI

from queryguard.export.reports import document_answer_docx_bytes, document_answer_markdown
from queryguard.export.tabular import dataframe_to_csv_bytes, dataframe_to_xlsx_bytes
from queryguard.models import DocumentQueryResponse


def _setting(name: str, default: str = "") -> str:
    """Read deployment settings from environment first, then Streamlit secrets."""
    env_value = os.getenv(name)
    if env_value:
        return env_value
    try:
        value = st.secrets.get(name, default)
    except FileNotFoundError:
        return default
    return str(value) if value is not None else default


API_URL = _setting("QUERYGUARD_API_URL", "http://localhost:8000").rstrip("/")
API_ACCESS_KEY = _setting("QUERYGUARD_API_ACCESS_KEY", "")
API = QueryGuardAPI(API_URL, API_ACCESS_KEY)


MODE_HELP = {
    "Try Demo": "Use the bundled Chinook SQLite database. No file upload is needed.",
    "Database": "Upload one SQLite database (.db, .sqlite, .sqlite3).",
    "Spreadsheet": "Upload one Excel (.xlsx) or CSV file. QueryGuard converts it to temporary SQLite.",
    "Documents": "Upload PDF, Word, or PowerPoint files and ask evidence-grounded questions.",
    "Invoices": "Upload invoice PDFs, images, Excel, or CSV files for normalized analytics and document lookup.",
}


st.set_page_config(
    page_title="QueryGuard AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    .qg-card {
        border: 1px solid rgba(128,128,128,.25);
        border-radius: 14px;
        padding: 1rem 1.1rem;
        margin-bottom: .75rem;
    }
    .qg-small {opacity: .75; font-size: .92rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def _workspace_key(mode: str) -> str:
    return f"workspace::{mode.lower()}"


def _get_workspace(mode: str) -> dict | None:
    return st.session_state.get(_workspace_key(mode))


def _set_workspace(mode: str, value: dict | None) -> None:
    key = _workspace_key(mode)
    if value is None:
        st.session_state.pop(key, None)
    else:
        st.session_state[key] = value


def _show_backend_status() -> dict | None:
    health = API.health()
    with st.sidebar:
        st.subheader("System status")
        if health:
            st.success("Backend connected")
            st.write(f"**Provider:** {health.get('llm_provider', 'unknown')}")
            st.write(f"**Model:** {health.get('llm_model', 'unknown')}")
            st.write(f"**Retrieval:** {health.get('retrieval_strategy', 'unknown')}")
            protection = "enabled" if health.get("api_protected") else "disabled"
            st.write(f"**API protection:** {protection}")
            st.caption(
                "Upload limits: "
                f"{health.get('max_upload_mb', '?')} MB/file · "
                f"{health.get('max_total_upload_mb', '?')} MB/workspace · "
                f"{health.get('max_upload_files', '?')} files"
            )
            ocr_status = "available" if health.get("ocr_available") else "not installed"
            st.caption(f"Image/scanned-document OCR: {ocr_status}")
        else:
            st.error("Backend is not reachable yet.")
            st.caption(
                "Check QUERYGUARD_API_URL. A sleeping free backend may also need a short cold start."
            )

        st.divider()
        st.subheader("LLM choices")
        st.caption(
            "Demo = deterministic smoke tests · Ollama = local/offline · "
            "Gemini = recommended hosted option · Groq = hosted alternative."
        )
        st.caption(
            "Provider changes are made in .env or deployment secrets, then the API is restarted."
        )
        with st.expander("How to change the AI provider"):
            st.code(
                "QUERYGUARD_LLM_PROVIDER=ollama\nQUERYGUARD_OLLAMA_MODEL=qwen2.5-coder:7b",
                language="text",
            )
            st.caption(
                "Use provider=gemini or provider=groq with its server-side API key for online mode. "
                "The public UI never displays provider secrets."
            )

        st.divider()
        st.subheader("Safety model")
        st.caption(
            "Generated SQL never executes directly. QueryGuard parses it, enforces a read-only policy, "
            "checks table access, and executes through a SQLite read-only connection with row/time limits."
        )
    return health


def _show_workspace_summary(workspace: dict) -> None:
    st.success(f"Active workspace: {workspace['display_name']}")
    columns = st.columns(4)
    if workspace.get("database_available"):
        columns[0].metric("Tables", workspace.get("table_count", 0))
        columns[1].metric("Columns", workspace.get("column_count", 0))
        columns[2].metric("Relationships", workspace.get("relationship_count", 0))
    if workspace.get("document_available"):
        columns[3].metric("Evidence chunks", workspace.get("document_chunk_count", 0))
    if workspace.get("invoice_count"):
        columns[0].metric("Invoices", workspace.get("invoice_count", 0))

    warnings = workspace.get("warnings") or []
    if warnings:
        with st.expander(f"Ingestion warnings ({len(warnings)})"):
            for warning in warnings:
                st.warning(warning)


def _workspace_uploader(
    *,
    mode: str,
    api_mode: str,
    extensions: list[str],
    multiple: bool,
    guidance: str,
) -> dict | None:
    workspace = _get_workspace(mode)
    if workspace:
        _show_workspace_summary(workspace)
        if st.button("Change source", key=f"change-{mode}"):
            try:
                API.delete_workspace(workspace["workspace_id"])
            except APIClientError:
                pass
            _set_workspace(mode, None)
            st.rerun()
        return workspace

    st.info(guidance)
    uploaded = st.file_uploader(
        "Choose file" if not multiple else "Choose one or more files",
        type=extensions,
        accept_multiple_files=multiple,
        key=f"upload-{mode}",
    )
    uploaded_files = uploaded if isinstance(uploaded, list) else ([uploaded] if uploaded else [])

    if st.button(
        "Create analysis workspace",
        type="primary",
        disabled=not uploaded_files,
        key=f"create-{mode}",
    ):
        try:
            with st.spinner("Validating files and preparing the workspace..."):
                workspace = API.upload_workspace(api_mode, uploaded_files)
        except APIClientError as exc:
            st.error(str(exc))
        else:
            _set_workspace(mode, workspace)
            st.rerun()
    return None


def _render_schema(workspace_id: str) -> None:
    with st.expander("View detected schema"):
        try:
            payload = API.workspace_schema(workspace_id)
        except APIClientError as exc:
            st.error(str(exc))
            return
        for table in payload.get("tables", []):
            st.markdown(f"**{table['name']}**")
            column_frame = pd.DataFrame(table.get("columns", []))
            if not column_frame.empty:
                st.dataframe(column_frame, use_container_width=True, hide_index=True)
            foreign_keys = table.get("foreign_keys", [])
            if foreign_keys:
                st.caption(
                    "Relationships: "
                    + "; ".join(
                        f"{item['from']} → {item['target_table']}.{item['target_column']}"
                        for item in foreign_keys
                    )
                )


def _render_query_response(data: dict, *, download_prefix: str = "queryguard_result") -> None:
    status = data.get("status")
    if status == "clarification":
        st.warning(data.get("clarification", "Please clarify the question."))
    elif status == "blocked":
        st.error("The generated query was blocked by the SQL safety policy.")
        if data.get("error"):
            st.caption(data["error"])
    elif status == "error":
        st.error(data.get("error", "The request could not be completed."))
    else:
        st.success("Query executed through the governed read-only pipeline.")

    sql = data.get("sql")
    if sql:
        st.subheader("Generated SQL")
        st.code(sql, language="sql")
        st.download_button(
            "Download SQL",
            data=sql.encode("utf-8"),
            file_name=f"{download_prefix}.sql",
            mime="text/plain",
        )

    validation = data.get("validation") or {}
    if validation:
        st.subheader("Governance checks")
        col1, col2, col3 = st.columns(3)
        col1.metric("Read-only policy", "Passed" if validation.get("is_safe") else "Blocked")
        col2.metric("Tables used", len(validation.get("tables", [])))
        col3.metric("Repair used", "Yes" if data.get("repaired") else "No")
        if validation.get("tables"):
            st.caption("Approved tables: " + ", ".join(validation["tables"]))

    rows = data.get("rows") or []
    columns = data.get("columns") or []
    if rows and columns:
        frame = pd.DataFrame(rows, columns=columns)
        st.subheader("Verified database result")
        chart_type = data.get("chart_type")
        if chart_type == "bar" and len(columns) >= 2:
            st.bar_chart(frame.set_index(columns[0])[columns[1]])
        elif chart_type == "line" and len(columns) >= 2:
            st.line_chart(frame.set_index(columns[0])[columns[1]])
        st.dataframe(frame, use_container_width=True, hide_index=True)

        export_col1, export_col2 = st.columns(2)
        export_col1.download_button(
            "Download CSV",
            data=dataframe_to_csv_bytes(frame),
            file_name=f"{download_prefix}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        export_col2.download_button(
            "Download Excel",
            data=dataframe_to_xlsx_bytes(frame),
            file_name=f"{download_prefix}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    if data.get("explanation"):
        st.subheader("Result explanation")
        st.write(data["explanation"])

    retrieved = data.get("retrieved_tables") or []
    if retrieved:
        with st.expander("Schema retrieval evidence"):
            st.dataframe(pd.DataFrame(retrieved), use_container_width=True, hide_index=True)

    latency = data.get("latency_ms") or {}
    if latency:
        with st.expander("Latency breakdown"):
            st.json(latency)


def _run_structured_query(workspace: dict, *, key_prefix: str, health: dict | None) -> None:
    if health and health.get("llm_provider") == "demo":
        st.warning(
            "Demo provider is deterministic and only knows a few Chinook examples. "
            "For arbitrary uploaded data, configure Ollama, Gemini, or Groq."
        )

    _render_schema(workspace["workspace_id"])
    question = st.text_input(
        "Ask a question about this data",
        placeholder="Example: Which products generated the most revenue?",
        key=f"question-{key_prefix}",
    )
    if st.button("Run governed analysis", type="primary", key=f"run-{key_prefix}"):
        if not question.strip():
            st.warning("Enter a question first.")
            return
        try:
            with st.spinner("Retrieving schema, generating SQL, validating, and executing..."):
                data = API.workspace_query(workspace["workspace_id"], question.strip())
        except APIClientError as exc:
            st.error(str(exc))
        else:
            _render_query_response(data, download_prefix=f"queryguard_{key_prefix}")


def _render_demo(health: dict | None) -> None:
    st.header("Try the built-in Chinook demo")
    st.write(
        "Chinook is a small digital-media store database. This mode demonstrates the original "
        "QueryGuard Text-to-SQL workflow without uploading any personal files."
    )
    steps = st.columns(4)
    steps[0].metric("1", "Retrieve schema")
    steps[1].metric("2", "Generate SQL")
    steps[2].metric("3", "Validate AST")
    steps[3].metric("4", "Execute read-only")

    examples = [
        "Show the top 5 customers by revenue",
        "Which countries generated the most revenue?",
        "Which genres have the most tracks?",
        "What is the average track price?",
        "How many customers are in the database?",
    ]
    selected = st.selectbox("Try an example", examples)
    question = st.text_input("Question", value=selected, key="demo-question")
    if st.button("Run demo query", type="primary", key="run-demo"):
        try:
            with st.spinner("Running governed query..."):
                data = API.demo_query(question)
        except APIClientError as exc:
            st.error(str(exc))
        else:
            _render_query_response(data, download_prefix="chinook_demo")

    if health and health.get("llm_provider") == "demo":
        st.caption(
            "You are using deterministic demo mode. Configure Ollama/Gemini/Groq to test free-form questions."
        )


def _render_database(health: dict | None) -> None:
    st.header("Analyze your SQLite database")
    st.write(
        "Upload a compatible SQLite file. QueryGuard validates the database, discovers its schema, "
        "builds a table retriever, and keeps query execution read-only."
    )
    workspace = _workspace_uploader(
        mode="Database",
        api_mode="database",
        extensions=["db", "sqlite", "sqlite3"],
        multiple=False,
        guidance="Accepted: .db, .sqlite, .sqlite3. The file is isolated in a temporary workspace.",
    )
    if workspace:
        _run_structured_query(workspace, key_prefix="database", health=health)


def _render_spreadsheet(health: dict | None) -> None:
    st.header("Analyze Excel or CSV data")
    st.write(
        "QueryGuard converts workbook sheets or a CSV table into temporary SQLite. "
        "The same Text-to-SQL governance pipeline then handles your questions."
    )
    workspace = _workspace_uploader(
        mode="Spreadsheet",
        api_mode="spreadsheet",
        extensions=["xlsx", "csv"],
        multiple=False,
        guidance=(
            "Excel: each non-empty sheet becomes a table. CSV: the file becomes one table. "
            "Macro-enabled spreadsheets are intentionally not accepted."
        ),
    )
    if workspace:
        _run_structured_query(workspace, key_prefix="spreadsheet", health=health)


def _render_documents(health: dict | None) -> None:
    st.header("Ask cited questions over documents")
    st.write(
        "PDF pages, Word sections, and PowerPoint slides are extracted into source-aware chunks. "
        "Only the most relevant chunks are sent to the LLM, and the UI shows the evidence used."
    )
    workspace = _workspace_uploader(
        mode="Documents",
        api_mode="document",
        extensions=["pdf", "docx", "pptx"],
        multiple=True,
        guidance="Upload one or more PDF, DOCX, or PPTX files. Scanned PDFs require optional OCR support.",
    )
    if not workspace:
        return

    if health and health.get("llm_provider") == "demo":
        st.info(
            "Demo mode can verify retrieval plumbing, but meaningful document answers require Ollama, Gemini, or Groq."
        )

    question = st.text_input(
        "Ask a question about the uploaded documents",
        placeholder="Example: What risks are discussed in the report?",
        key="document-question",
    )
    if st.button("Ask documents", type="primary", key="run-document"):
        if not question.strip():
            st.warning("Enter a question first.")
            return
        try:
            with st.spinner("Retrieving evidence and generating a grounded answer..."):
                data = API.document_query(workspace["workspace_id"], question.strip())
        except APIClientError as exc:
            st.error(str(exc))
            return

        if data.get("status") == "error":
            st.error(data.get("error", "Document analysis failed."))
            return

        st.success("Answer generated from retrieved document evidence.")
        st.subheader("Answer")
        st.write(data.get("answer", ""))

        sources = data.get("sources") or []
        st.subheader("Evidence")
        for index, source in enumerate(sources, start=1):
            with st.expander(f"Source {index}: {source['source_name']} — {source['locator']}"):
                st.write(source["excerpt"])
                st.caption(f"Retrieval score: {source['score']}")

        response_model = DocumentQueryResponse.model_validate(data)
        download_col1, download_col2 = st.columns(2)
        download_col1.download_button(
            "Download Markdown report",
            data=document_answer_markdown(response_model).encode("utf-8"),
            file_name="queryguard_document_analysis.md",
            mime="text/markdown",
            use_container_width=True,
        )
        download_col2.download_button(
            "Download Word report",
            data=document_answer_docx_bytes(response_model),
            file_name="queryguard_document_analysis.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )


def _render_invoices(health: dict | None) -> None:
    st.header("Invoice intelligence")
    st.write(
        "QueryGuard extracts a conservative set of invoice fields, flags uncertain records for review, "
        "stores normalized fields in SQLite for analytics, and keeps invoice text as evidence when available."
    )
    if health and not health.get("ocr_available"):
        st.warning(
            "OCR is not installed on this backend. Text PDFs, XLSX, and CSV invoices still work, "
            "but image/scanned invoices need Tesseract OCR. See docs/LOCAL_SETUP.md."
        )
    workspace = _workspace_uploader(
        mode="Invoices",
        api_mode="invoice",
        extensions=["pdf", "png", "jpg", "jpeg", "xlsx", "csv"],
        multiple=True,
        guidance=(
            "Text PDFs and spreadsheet invoices work with normal Python dependencies. "
            "PNG/JPG and scanned invoices require optional Tesseract OCR."
        ),
    )
    if not workspace:
        return

    try:
        records_payload = API.invoice_records(workspace["workspace_id"])
    except APIClientError as exc:
        st.error(str(exc))
        return

    records = records_payload.get("records") or []
    if records:
        frame = pd.DataFrame(records)
        st.subheader("Normalized invoice records")
        st.dataframe(frame, use_container_width=True, hide_index=True)
        review_count = int(frame.get("needs_review", pd.Series(dtype=bool)).sum())
        st.caption(
            f"{len(frame)} record(s) extracted; {review_count} flagged for manual review. "
            "Extraction is intentionally conservative rather than silently guessing missing values."
        )
        col1, col2 = st.columns(2)
        col1.download_button(
            "Download invoice CSV",
            data=dataframe_to_csv_bytes(frame),
            file_name="queryguard_invoices.csv",
            mime="text/csv",
            use_container_width=True,
        )
        col2.download_button(
            "Download invoice Excel",
            data=dataframe_to_xlsx_bytes(frame, sheet_name="Invoices"),
            file_name="queryguard_invoices.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    analytics_tab, evidence_tab = st.tabs(["Analytics", "Invoice text Q&A"])
    with analytics_tab:
        _run_structured_query(workspace, key_prefix="invoices", health=health)

    with evidence_tab:
        if not workspace.get("document_available"):
            st.info(
                "This workspace was created from structured spreadsheet rows, so there is no raw document text to search."
            )
        else:
            question = st.text_input(
                "Ask about wording in the invoice documents",
                placeholder="Example: What payment terms are written on invoice INV-1008?",
                key="invoice-document-question",
            )
            if st.button("Search invoice text", key="run-invoice-document"):
                if not question.strip():
                    st.warning("Enter a question first.")
                else:
                    try:
                        data = API.document_query(workspace["workspace_id"], question.strip())
                    except APIClientError as exc:
                        st.error(str(exc))
                    else:
                        if data.get("status") == "error":
                            st.error(data.get("error", "Invoice document query failed."))
                        else:
                            st.write(data.get("answer", ""))
                            for source in data.get("sources") or []:
                                st.caption(f"{source['source_name']} — {source['locator']}")
                                st.write(source["excerpt"])


health = _show_backend_status()

st.title("🛡️ QueryGuard AI")
st.caption("Governed Data & Document Intelligence Platform")
st.write(
    "Ask questions over databases and spreadsheets with governed Text-to-SQL, "
    "or query documents with evidence-grounded retrieval. The built-in Chinook database remains the demo."
)

st.subheader("Choose an analysis workspace")
card_columns = st.columns(4)
card_content = [
    ("🗄️ Database", "SQLite / DB", "Dynamic schema → governed Text-to-SQL"),
    ("📊 Spreadsheet", "Excel / CSV", "Convert to SQLite → governed analytics"),
    ("📄 Documents", "PDF / DOCX / PPTX", "Retrieve evidence → cited answer"),
    ("🧾 Invoices", "PDF / image / XLSX / CSV", "Extract fields → analytics + evidence"),
]
for column, (title, source, workflow) in zip(card_columns, card_content, strict=True):
    with column:
        st.markdown(
            f"<div class='qg-card'><strong>{title}</strong><br>"
            f"<span class='qg-small'>{source}</span><br><br>{workflow}</div>",
            unsafe_allow_html=True,
        )

with st.expander("How QueryGuard decides what to do"):
    st.markdown(
        "**Structured data** (demo/SQLite/Excel/CSV) uses schema retrieval → LLM SQL → "
        "SQLGlot validation → read-only SQLite.  \n"
        "**Documents** use parsing → chunks → retrieval → LLM answer + source evidence.  \n"
        "**Invoices** combine both: normalized fields become SQLite while raw text can be searched as evidence."
    )

mode = st.radio(
    "Choose what you want to analyze",
    list(MODE_HELP),
    horizontal=True,
)
st.caption(MODE_HELP[mode])
st.divider()

if mode == "Try Demo":
    _render_demo(health)
elif mode == "Database":
    _render_database(health)
elif mode == "Spreadsheet":
    _render_spreadsheet(health)
elif mode == "Documents":
    _render_documents(health)
else:
    _render_invoices(health)

st.divider()
st.caption(
    "Portfolio scope: personal/local analysis and demonstration. Uploaded workspaces are temporary. "
    "Do not use the public demo for confidential or regulated data."
)
