# Security

QueryGuard treats generated SQL and uploaded files as untrusted input.

## Controls in this repository

- Generated SQL is parsed and restricted to a single read-only SELECT-style statement.
- Referenced database tables must exist in the discovered schema.
- SQLite query execution uses a read-only connection and `PRAGMA query_only = ON`.
- Query time and returned row count are limited.
- Upload count, per-file size, combined size and Office archive expansion are limited.
- Runtime workspaces expire and are excluded from version control.
- Excel exports prefix formula-like text to reduce spreadsheet formula injection risk.
- API keys are read from environment variables and are not stored in source code.
- An optional API access key can protect query and upload endpoints.

## Deployment guidance

A public demo should use non-sensitive data. Files are temporarily stored on the service filesystem while a workspace is active, so this project should not be used as-is for confidential or regulated data.

Use HTTPS at the hosting layer, configure `QUERYGUARD_API_ACCESS_KEY`, restrict service access where possible, and use a dedicated secret manager for model API credentials.

## Reporting a vulnerability

Please open a private security report through GitHub Security Advisories rather than posting credentials or exploit details in a public issue.
