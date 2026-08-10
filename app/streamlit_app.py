"""Recruiter-facing Streamlit demo for QueryGuard AI."""

from __future__ import annotations

import os

import httpx
import pandas as pd
import streamlit as st


def _setting(name: str, default: str = "") -> str:
    """Read a deployment setting from env first, then Streamlit secrets."""
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


def _headers() -> dict[str, str]:
    if not API_ACCESS_KEY:
        return {}
    return {"X-QueryGuard-Key": API_ACCESS_KEY}


def _backend_health() -> dict | None:
    try:
        response = httpx.get(f"{API_URL}/health", timeout=45)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return None


st.set_page_config(page_title="QueryGuard AI", page_icon="🛡️", layout="wide")
st.title("🛡️ QueryGuard AI")
st.caption("Governed Text-to-SQL Analytics Copilot")

health = _backend_health()
with st.sidebar:
    st.subheader("System status")
    if health:
        st.success("Backend connected")
        st.write(f"**LLM:** {health.get('llm_provider', 'unknown')}")
        st.write(f"**Model:** {health.get('llm_model', 'unknown')}")
        st.write(f"**Retrieval:** {health.get('retrieval_strategy', 'unknown')}")
        st.write("**Database:** read-only Chinook SQLite")
        st.write(
            "**API protection:** "
            + ("enabled" if health.get("api_protected") else "disabled")
        )
    else:
        st.error("Backend is not reachable yet.")
        st.caption("A free Render service may need a short cold start after inactivity.")

    st.divider()
    st.subheader("Why this is governed")
    st.write(
        "The LLM can propose SQL, but it cannot execute arbitrary database operations. "
        "SQL is parsed, checked against a read-only policy, and then executed with row and time limits."
    )

st.info(
    "Demo dataset: Chinook digital media store. Ask analytical questions about customers, "
    "invoices, tracks, artists, albums, genres, and sales."
)

examples = [
    "Show the top 5 customers by revenue",
    "Which countries generated the most revenue?",
    "Which genres have the most tracks?",
    "What is the average track price?",
    "How many customers are in the database?",
]

selected_example = st.selectbox("Try an example", examples, index=0)
question = st.text_input(
    "Ask a question about the Chinook database",
    value=selected_example,
    max_chars=2000,
)

if st.button("Run governed query", type="primary", use_container_width=True):
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        with st.spinner("Retrieving schema, generating SQL, validating, and executing..."):
            try:
                response = httpx.post(
                    f"{API_URL}/query",
                    headers=_headers(),
                    json={"question": question.strip()},
                    timeout=180,
                )
                if response.status_code == 401:
                    st.error(
                        "The hosted UI and API access keys do not match. "
                        "Check the Streamlit and Render secret settings."
                    )
                    st.stop()
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as exc:
                st.error(f"Could not complete the QueryGuard request: {exc}")
            else:
                status = data.get("status")
                if status == "clarification":
                    st.warning(data.get("clarification", "Please clarify the question."))
                elif status == "blocked":
                    st.error("The generated query was blocked by the SQL safety policy.")
                    st.caption(data.get("error", ""))
                elif status == "error":
                    st.error(data.get("error", "The request could not be completed."))
                else:
                    st.success("Query executed through the governed read-only pipeline.")

                sql = data.get("sql")
                if sql:
                    st.subheader("Generated SQL")
                    st.code(sql, language="sql")

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
                    st.dataframe(frame, use_container_width=True)

                if data.get("explanation"):
                    st.subheader("Result explanation")
                    st.write(data["explanation"])

                retrieved = data.get("retrieved_tables") or []
                if retrieved:
                    with st.expander("Schema retrieval evidence"):
                        st.dataframe(pd.DataFrame(retrieved), use_container_width=True)

                latency = data.get("latency_ms") or {}
                if latency:
                    with st.expander("Latency breakdown"):
                        st.json(latency)
