"""HTTP client used by the Streamlit interface."""

from __future__ import annotations

from typing import Any

import httpx


class APIClientError(RuntimeError):
    pass


class QueryGuardAPI:
    def __init__(self, base_url: str, access_key: str = "", timeout: float = 90.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {"X-QueryGuard-Key": access_key} if access_key else {}

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = dict(self.headers)
        headers.update(kwargs.pop("headers", {}))
        try:
            response = httpx.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise APIClientError(f"Backend request failed: {exc}") from exc
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise APIClientError(f"Backend returned {response.status_code}: {detail}")
        if not response.content:
            return None
        return response.json()

    def health(self) -> dict | None:
        try:
            return self._request("GET", "/health")
        except APIClientError:
            return None

    def demo_query(self, question: str) -> dict:
        return self._request("POST", "/query", json={"question": question})

    def upload_workspace(self, mode: str, uploaded_files: list[Any]) -> dict:
        files = [
            ("files", (file.name, file.getvalue(), getattr(file, "type", None) or "application/octet-stream"))
            for file in uploaded_files
        ]
        return self._request("POST", "/workspaces/upload", data={"mode": mode}, files=files)

    def delete_workspace(self, workspace_id: str) -> None:
        self._request("DELETE", f"/workspaces/{workspace_id}")

    def workspace_schema(self, workspace_id: str) -> dict:
        return self._request("GET", f"/workspaces/{workspace_id}/schema")

    def workspace_query(self, workspace_id: str, question: str) -> dict:
        return self._request(
            "POST",
            f"/workspaces/{workspace_id}/query",
            json={"question": question},
        )

    def document_query(self, workspace_id: str, question: str) -> dict:
        return self._request(
            "POST",
            f"/workspaces/{workspace_id}/document-query",
            json={"question": question},
        )

    def invoice_records(self, workspace_id: str) -> dict:
        return self._request("GET", f"/workspaces/{workspace_id}/invoice-records")
