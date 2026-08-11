# API Reference

The FastAPI service exposes the Chinook demo and temporary uploaded workspaces. Interactive OpenAPI documentation is available at `/docs` while the API is running.

If `QUERYGUARD_API_ACCESS_KEY` is configured, protected endpoints require:

```text
X-QueryGuard-Key: <shared-secret>
```

`/health` remains public so the hosted UI can diagnose backend availability without exposing a provider key.

## `GET /health`

Purpose: deployment and UI health information.

Returns provider/model/retrieval metadata, demo database availability, API-protection status, configured upload/workspace limits, OCR availability, and supported source types. It never returns secrets.

## `GET /schema`

Purpose: inspect the built-in Chinook demo schema.

Returns tables, columns, primary-key flags, and foreign-key relationships.

## `POST /query`

Purpose: query the built-in Chinook demo.

Example request:

```json
{
  "question": "Show the top 5 customers by revenue",
  "top_k_tables": 5
}
```

The response can contain generated SQL, validation details, database rows, presentation metadata, retrieved schema context, repair status, and latency.

## `POST /workspaces/upload`

Multipart upload endpoint.

Fields:

- `mode`: `database`, `spreadsheet`, `document`, or `invoice`;
- `files`: one or more uploaded files according to the selected mode.

The endpoint enforces per-file size, combined upload size, and file-count limits before ingestion.

The response is `WorkspaceInfo`, containing a random workspace ID plus detected capabilities/counts/warnings.

## `GET /workspaces/{workspace_id}`

Returns current temporary workspace metadata.

Workspace IDs are server-generated 32-character lowercase hexadecimal IDs. Arbitrary filesystem paths are never accepted by this API.

## `DELETE /workspaces/{workspace_id}`

Deletes the temporary workspace. The Streamlit `Change source` action uses this endpoint before clearing local UI state.

## `GET /workspaces/{workspace_id}/schema`

Available for a workspace that contains a database (uploaded SQLite, spreadsheet-generated SQLite, or invoice-normalized SQLite).

Returns the same schema shape as `/schema`.

## `POST /workspaces/{workspace_id}/query`

Runs the governed Text-to-SQL workflow against the workspace database.

This is used by Database, Spreadsheet, and structured Invoice analytics modes.

The SQL-generation provider is selected by backend configuration. The SQL is always revalidated against the active workspace schema before read-only execution.

## `POST /workspaces/{workspace_id}/document-query`

Example request:

```json
{
  "question": "What payment terms are mentioned?",
  "top_k": 5
}
```

Loads the workspace chunks, retrieves evidence, asks the configured LLM to answer only from that evidence, and returns both answer and evidence metadata.

Used by Documents and the document side of Invoice mode.

## `GET /workspaces/{workspace_id}/invoice-records`

Returns normalized public invoice fields. `raw_text` is excluded from this endpoint.

The UI uses these records for review indicators and CSV/XLSX export.

## Error behavior

Common status codes:

- `400` — invalid source/ingestion/workspace operation;
- `401` — missing/incorrect hosted shared key;
- `404` — workspace missing/expired;
- `413` — file/count/combined upload limit exceeded;
- `503` — required LLM provider configuration is unavailable.

Model mistakes inside a successfully handled analytical request are normally represented in the structured `QueryResponse` status/error fields rather than by fabricating a successful answer.
