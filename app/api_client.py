"""Small HTTP client used by the Streamlit frontend."""

from __future__ import annotations

from typing import Any

import httpx


class APIClientError(RuntimeError):
    pass


class QueryGuardAPI:
    def __init__(self, base_url: str, access_key: str = "") -> None:
        self.base_url = base_url.rstrip("/")
        self.access_key = access_key

    def _headers(self) -> dict[str, str]:
        if not self.access_key:
            return {}
        return {"X-QueryGuard-Key": self.access_key}

    def _json(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code == 401:
            raise APIClientError(
                "The Streamlit and FastAPI access keys do not match. "
                "Check QUERYGUARD_API_ACCESS_KEY on both deployments."
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise APIClientError(str(detail)) from exc
        return response.json()

    def health(self) -> dict[str, Any] | None:
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=45)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            return None

    def demo_query(self, question: str) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/query",
            headers=self._headers(),
            json={"question": question},
            timeout=180,
        )
        return self._json(response)

    def upload_workspace(self, mode: str, uploaded_files) -> dict[str, Any]:
        files = [
            (
                "files",
                (uploaded.name, uploaded.getvalue(), uploaded.type or "application/octet-stream"),
            )
            for uploaded in uploaded_files
        ]
        response = httpx.post(
            f"{self.base_url}/workspaces/upload",
            headers=self._headers(),
            data={"mode": mode},
            files=files,
            timeout=180,
        )
        return self._json(response)

    def delete_workspace(self, workspace_id: str) -> None:
        response = httpx.delete(
            f"{self.base_url}/workspaces/{workspace_id}",
            headers=self._headers(),
            timeout=30,
        )
        self._json(response)

    def workspace_schema(self, workspace_id: str) -> dict[str, Any]:
        response = httpx.get(
            f"{self.base_url}/workspaces/{workspace_id}/schema",
            headers=self._headers(),
            timeout=60,
        )
        return self._json(response)

    def workspace_query(self, workspace_id: str, question: str) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/workspaces/{workspace_id}/query",
            headers=self._headers(),
            json={"question": question},
            timeout=180,
        )
        return self._json(response)

    def document_query(self, workspace_id: str, question: str) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url}/workspaces/{workspace_id}/document-query",
            headers=self._headers(),
            json={"question": question},
            timeout=180,
        )
        return self._json(response)

    def invoice_records(self, workspace_id: str) -> dict[str, Any]:
        response = httpx.get(
            f"{self.base_url}/workspaces/{workspace_id}/invoice-records",
            headers=self._headers(),
            timeout=60,
        )
        return self._json(response)
