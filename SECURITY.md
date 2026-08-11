# Security Policy and Portfolio Boundary

QueryGuard AI is a personal/portfolio analytics prototype. Its controls are real engineering controls, but they are **not** a claim of enterprise certification or a safe place for confidential production data.

## Implemented controls

- SQLGlot AST inspection before generated SQL is executed.
- Single read-only SELECT-style statement policy.
- Active-database table allowlist.
- SQLite `mode=ro` plus `PRAGMA query_only=ON` during analytical execution.
- Query timeout and result-row cap.
- Security-policy failures are not sent through the automatic repair path.
- Random 32-character workspace identifiers.
- User filenames are reduced to safe basenames; request paths cannot select arbitrary server files.
- File-extension allowlists.
- Per-file, combined-upload, and file-count limits.
- Office ZIP member/uncompressed-size limits.
- Uploaded SQLite integrity validation.
- Temporary workspaces expire and are excluded from Git.
- Real `.env` and Streamlit secret files are excluded from Git.
- Optional shared `X-QueryGuard-Key` between the hosted UI and API.
- Document prompts explicitly treat uploaded text as untrusted evidence rather than instructions.
- CSV/XLSX downloads escape formula-like text before spreadsheet export.

## Important limitations

The project does not implement enterprise user identity, row/column-level authorization, malware scanning, a WAF, tenant-grade storage isolation, durable audit logging, KMS-managed encryption, legal-retention controls, or per-user rate limiting.

The shared UI/API key is only an app-to-app preview control. It does not identify individual users.

OCR and document parsers may process malformed or adversarial files differently across library versions. File limits reduce risk but are not a substitute for a production file-scanning service.

Generated SQL can be structurally safe and still answer the wrong business question. Important decisions require review of the generated SQL, evidence, and business definitions.

## Secrets

Never commit or paste these values into source files:

```text
QUERYGUARD_GEMINI_API_KEY
QUERYGUARD_GROQ_API_KEY
QUERYGUARD_API_ACCESS_KEY
```

Use `.env` locally, Render environment variables for the API, and Streamlit Community Cloud secrets for the frontend.

## Public demo data

The hosted portfolio version should use Chinook or other public/non-sensitive files. Before sending private material to a hosted LLM provider, review the provider's current privacy/data-use terms and your organization's policy.

For the detailed threat model and mitigations, see [`docs/SECURITY.md`](docs/SECURITY.md).
