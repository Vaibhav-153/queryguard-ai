# Troubleshooting

## Streamlit says backend is not reachable

1. Open `<API_URL>/health` directly.
2. If it fails, inspect FastAPI/Render logs.
3. Verify `QUERYGUARD_API_URL` is the base URL only — not `/health` or `/query`.
4. If hosted on a sleeping service, wait for cold start and retry.

## UI/API access keys do not match

The same raw value must exist in both services.

Render:

```text
QUERYGUARD_API_ACCESS_KEY=abc123
```

Streamlit:

```toml
QUERYGUARD_API_ACCESS_KEY = "abc123"
```

Save/deploy Render and reboot Streamlit.

## Gemini provider configuration error

Verify:

```text
QUERYGUARD_LLM_PROVIDER=gemini
QUERYGUARD_GEMINI_API_KEY=<real secret>
QUERYGUARD_GEMINI_MODEL=gemini-3.5-flash
```

Restart FastAPI after changing `.env`.

## Ollama connection error

Check:

```bash
ollama list
```

Then:

```text
http://localhost:11434/api/tags
```

Verify model name in `.env` exactly matches an installed model.

## Uploaded SQLite rejected

Possible causes:

- unsupported extension;
- corrupt/non-SQLite file renamed to `.db`;
- no user tables;
- upload above configured size.

QueryGuard runs SQLite `quick_check`; do not disable it just to make a file pass.

## Excel workbook rejected

Only `.xlsx` is accepted. `.xlsm`/macro-enabled formats are intentionally excluded.

Very large Office ZIP expansion can also be rejected.

## Multi-sheet Excel query generates bad join

Excel does not contain declared foreign-key relationships. Use descriptive column names, convert the data to a real relational SQLite schema, or add explicit relationship support before relying on multi-table joins.

## PDF says OCR is required

The PDF contains no extractable text.

Install:

```bash
pip install -e ".[ocr]"
```

and install the Tesseract system binary.

Verify:

```bash
tesseract --version
```

## Invoice image rejected

PNG/JPG invoice extraction requires OCR. Use a text PDF/structured XLSX/CSV or install Tesseract.

## SQLGlot missing

Core installation should include SQLGlot:

```bash
pip install -e .
```

If the environment cannot access PyPI, AST tests/query execution cannot be fully verified there. Do not replace SQLGlot with regex as a shortcut.

## Chinook checksum mismatch

Run:

```bash
python scripts/setup_chinook.py
```

The script normalizes line endings before hashing. A mismatch after normalization means the SQL source actually differs; investigate before changing the expected hash.

## GitHub Actions Ruff failure

Local/Codespaces:

```bash
ruff check app src tests scripts --fix
ruff format app src tests scripts
ruff check app src tests scripts
ruff format --check app src tests scripts
```

Review the diff, then commit.

## Tests skip SQL governance

If `sqlglot` is not installed, SQLGlot-dependent tests intentionally skip in constrained artifact environments. In a normal GitHub Actions run, `pip install -e ".[ui,dev]"` installs it and those tests should run.
