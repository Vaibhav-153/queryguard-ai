# QueryGuard AI

QueryGuard AI is a Python application for asking natural-language questions over local structured data and documents. For database questions it retrieves relevant schema, generates one SQLite query, validates the SQL, and executes it through a read-only connection. It also supports spreadsheet uploads, cited document questions, and basic invoice extraction.

The repository includes a deterministic demo provider, so the main pipeline can be tested without an API key.

## What it does

- **Text-to-SQL:** ask questions over SQLite databases.
- **Spreadsheet analysis:** convert CSV or Excel sheets to a temporary SQLite workspace before querying.
- **Document Q&A:** extract text from PDF, DOCX, and PPTX files and return answers with retrieved passages.
- **Invoice analysis:** normalize fields from CSV/XLSX invoices and extract conservative fields from PDF/image invoices.
- **API and UI:** FastAPI backend with a Streamlit interface.

## SQL safety pipeline

Database questions follow this path:

1. Inspect the SQLite schema.
2. Rank relevant tables with a lexical retriever.
3. Ask the configured model for one SQLite query.
4. Parse and validate SQL with SQLGlot.
5. Reject non-read-only operations, multiple statements, and tables outside the discovered schema.
6. Execute through a SQLite `mode=ro` connection with `PRAGMA query_only = ON`.
7. Apply a query timeout and result-row limit.
8. Optionally attempt one repair when generation or execution fails for a non-security reason.

The validator is a guardrail, not a database permission system. Uploaded data should still be treated as untrusted, and public deployments should not be used for sensitive files.

## Project structure

```text
queryguard-ai/
├── app/                    # Streamlit client
├── data/                   # Generated demo database (runtime workspaces are ignored)
├── docs/                   # Architecture and evaluation notes
├── examples/               # Small CSV examples
├── results/                # Reproducible retrieval evaluation output
├── scripts/                # Demo setup, verification and evaluation
├── src/queryguard/         # Core package and FastAPI application
├── tests/                  # Unit and integration tests
├── Dockerfile              # API container used by Render
├── pyproject.toml
├── render.yaml
└── README.md
```

## Installation

Python 3.11 or newer is required. Python 3.12 is used by the included CI workflow.

```bash
python -m venv .venv
```

Activate the environment, then install the application and development tools:

```bash
pip install -e ".[ui,dev]"
```

For OCR support on image invoices or scanned PDF pages, install the optional Python dependency and Tesseract on the operating system:

```bash
pip install -e ".[ocr]"
```

## Run locally

Create the synthetic demo database:

```bash
python scripts/setup_demo_db.py
```

Start the API:

```bash
uvicorn queryguard.api:app --reload
```

In another terminal, point the Streamlit client at the API and run it:

```bash
export QUERYGUARD_API_URL=http://127.0.0.1:8000
streamlit run app/streamlit_app.py
```

On Windows PowerShell, use:

```powershell
$env:QUERYGUARD_API_URL="http://127.0.0.1:8000"
streamlit run app/streamlit_app.py
```

The API exposes interactive OpenAPI documentation at `/docs` while it is running.

## Model providers

`QUERYGUARD_LLM_PROVIDER` can be set to:

- `demo` — deterministic local behavior for the bundled examples and basic previews.
- `gemini` — Google Gemini API.
- `groq` — Groq-compatible chat completion API.
- `ollama` — local Ollama server.

Copy `.env.example` to `.env` and set only the provider variables you need. Do not commit API keys.

The demo provider is intentionally limited. Use a configured model provider for free-form questions over arbitrary uploaded schemas.

## API examples

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Demo question:

```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"Show the top 5 customers by revenue"}'
```

If `QUERYGUARD_API_ACCESS_KEY` is configured, protected endpoints require the `X-QueryGuard-Key` header.

## Tests

```bash
ruff check app src tests scripts
python -m compileall -q src app tests scripts
pytest
queryguard-verify
```

The tests cover SQL validation, read-only database access, schema retrieval, uploads, document evidence retrieval, invoice normalization, workspaces, exports, the API, and the deterministic demo flow.

## Retrieval evaluation

`python scripts/evaluate_retrieval.py` evaluates table retrieval on five synthetic demo questions and writes `results/retrieval_metrics.json`.

The current reproducible results are:

| Metric | Result |
| --- | ---: |
| Mean Recall@1 | 0.800 |
| Mean Recall@3 | 1.000 |
| Mean Recall@5 | 1.000 |

This is a five-question synthetic check for the bundled schema, not a benchmark of Text-to-SQL quality on external datasets. See [docs/EVALUATION.md](docs/EVALUATION.md).

## Limitations

- SQL generation quality depends on the configured model and the database schema.
- The lexical schema retriever is small and explainable, but it is not semantic retrieval.
- Document retrieval is lexical and does not use embeddings.
- OCR depends on a local Tesseract installation and may require manual review.
- Invoice extraction is conservative and does not replace accounting verification.
- Only SQLite is supported for query execution.
- Workspaces are filesystem-backed and designed for a single service instance, not multi-node storage.

## Deployment

`render.yaml` and `Dockerfile` configure the FastAPI service. The Streamlit UI can be deployed separately by setting `QUERYGUARD_API_URL` to the API address.

For a public deployment, set an API access key, use non-sensitive test files, and review upload limits before exposing the service.

## License

MIT License. See [LICENSE](LICENSE).
