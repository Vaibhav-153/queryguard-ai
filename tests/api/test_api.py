import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from queryguard.api.main import create_app
from queryguard.config import Settings

SQLGLOT_AVAILABLE = importlib.util.find_spec("sqlglot") is not None


def _settings(database_path: Path, workspace_root: Path, **overrides) -> Settings:
    values = {
        "environment": "test",
        "database_path": database_path,
        "workspace_root": workspace_root,
        "llm_provider": "demo",
        "retrieval_strategy": "lexical",
    }
    values.update(overrides)
    return Settings(**values)


def test_health_reports_runtime_capabilities(database_path, tmp_path):
    client = TestClient(create_app(_settings(database_path, tmp_path / "workspaces")))

    health = client.get("/health")
    assert health.status_code == 200
    payload = health.json()
    assert payload["database_available"] is True
    assert payload["llm_model"] == "deterministic-demo"
    assert isinstance(payload["ocr_available"], bool)
    assert payload["max_upload_files"] >= 1


@pytest.mark.skipif(not SQLGLOT_AVAILABLE, reason="SQLGlot required for query endpoint.")
def test_demo_query_with_demo_provider(database_path, tmp_path):
    client = TestClient(create_app(_settings(database_path, tmp_path / "workspaces")))

    response = client.post(
        "/query",
        json={"question": "How many customers are in the database?"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["rows"] == [[59]]
    assert payload["validation"]["is_safe"] is True


def test_query_endpoint_can_require_shared_access_key(database_path, tmp_path):
    settings = _settings(
        database_path,
        tmp_path / "workspaces",
        api_access_key=SecretStr("secret-test-key"),
    )
    client = TestClient(create_app(settings))

    blocked = client.get("/workspaces/missing")
    assert blocked.status_code == 401

    allowed = client.get(
        "/workspaces/missing",
        headers={"X-QueryGuard-Key": "secret-test-key"},
    )
    assert allowed.status_code == 404


def test_upload_document_workspace(database_path, tmp_path):
    settings = _settings(database_path, tmp_path / "workspaces")
    client = TestClient(create_app(settings))

    import fitz

    pdf_path = tmp_path / "sample.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Annual leave policy provides 20 days of leave.")
    document.save(pdf_path)
    document.close()

    response = client.post(
        "/workspaces/upload",
        data={"mode": "document"},
        files={"files": ("sample.pdf", pdf_path.read_bytes(), "application/pdf")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["document_available"] is True
    assert payload["document_chunk_count"] >= 1


def test_uploaded_document_can_be_queried_in_demo_mode(database_path, tmp_path):
    settings = _settings(database_path, tmp_path / "workspaces")
    client = TestClient(create_app(settings))

    import fitz

    pdf_path = tmp_path / "policy.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Annual leave policy provides 20 days of leave.")
    document.save(pdf_path)
    document.close()

    upload = client.post(
        "/workspaces/upload",
        data={"mode": "document"},
        files={"files": ("policy.pdf", pdf_path.read_bytes(), "application/pdf")},
    )
    workspace_id = upload.json()["workspace_id"]

    response = client.post(
        f"/workspaces/{workspace_id}/document-query",
        json={"question": "What does the annual leave policy provide?", "top_k": 3},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["sources"][0]["source_name"] == "policy.pdf"
    assert "Page 1" in payload["sources"][0]["locator"]


def test_upload_file_count_limit_is_enforced(database_path, tmp_path):
    settings = _settings(
        database_path,
        tmp_path / "workspaces",
        max_upload_files=1,
    )
    client = TestClient(create_app(settings))

    response = client.post(
        "/workspaces/upload",
        data={"mode": "document"},
        files=[
            ("files", ("one.pdf", b"not parsed", "application/pdf")),
            ("files", ("two.pdf", b"not parsed", "application/pdf")),
        ],
    )

    assert response.status_code == 413
    assert "At most 1 files" in response.json()["detail"]
