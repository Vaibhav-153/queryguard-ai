# Build verification

Date: 2026-08-10
Version: QueryGuard AI 1.1.0 cloud-preview edition

This report separates what was actually executed in the artifact-build environment from what still requires a normal GitHub/cloud environment.

## Environment

- Python: 3.13.5 in the artifact-build runtime.
- Repository target: Python 3.11+.
- Bundled demo database: Chinook 1.4.5 SQLite.
- Cloud providers implemented: Gemini, Groq.
- Local provider retained: Ollama.

## Cloud deployment changes — Implemented

- Gemini REST provider with configurable model/key/thinking level.
- Groq OpenAI-compatible REST provider with configurable model/key.
- Ollama provider preserved for local/offline mode.
- provider factory supports `ollama`, `gemini`, `groq`, and `demo`.
- `/query` can require `X-QueryGuard-Key`.
- Render Blueprint (`render.yaml`) added.
- Render runtime reads the platform `PORT` value.
- Streamlit reads backend URL/access key from environment or Community Cloud secrets.
- `.streamlit/secrets.toml` is ignored by Git; example file included.
- cloud deployment guide added.
- hosted retrieval defaults to the lightweight measured lexical baseline.

## Critical dependency correction — Fixed

The earlier repository declared `sqlglot>=30.15,<31.0`, but that release line was not available at packaging time. The project now declares:

```text
sqlglot>=30.13,<31.0
```

This prevents a fresh public-PyPI cloud build from requesting a nonexistent minimum release.

## Data verification — Measured

`python scripts/setup_chinook.py` completed successfully from the bundled official SQL source.

- SQLite file size: 1,007,616 bytes.
- SQL SHA-256: `fdcb271b3e9c840216b09168752bddca973ed3917b40e49b603b15831114aea1`
- SQLite SHA-256: `79df86ebd5c45f009ed35dbb19757cac4f9afb393352e3d2ffe128a60a2ea718`
- Customers: 59.
- Tracks: 3,503.
- Total invoice revenue check: 2328.60.

## Python compile check — Passed

Executed:

```bash
python -m compileall -q src app tests scripts
```

Result: passed with no syntax errors.

## Test suite — Partially executed because of runtime dependency availability

Executed:

```bash
pytest -q -rs
```

Result:

- **17 tests passed**.
- **3 test modules skipped at collection** because `sqlglot` is not installed in this artifact-build runtime.
- Skipped modules: full API pipeline, QueryService integration, and SQLGlot security tests.
- The 17 executed tests include the mocked Gemini/Groq provider tests and missing-key factory validation.

The runtime's configured Python package index does not supply SQLGlot and outbound access to public PyPI is blocked. Public PyPI currently has the compatible SQLGlot release targeted by this repository, so GitHub/Render are expected to install it through normal internet package resolution. This expectation is not represented as a locally executed result.

## Retrieval baseline — Measured after cloud changes

Executed:

```bash
PYTHONPATH=src python scripts/evaluate_retrieval.py
```

15 custom Chinook questions:

- Table Recall@1: **0.800**
- Table Recall@3: **0.967**
- Table Recall@5: **0.967**

Full per-example records: `results/lexical_retrieval_baseline.json`.

## Render configuration parse — Passed

`render.yaml` was parsed locally as YAML and contains the expected `queryguard-api` service, build command, `$PORT` start command, health path, Gemini secret placeholder, and generated QueryGuard access key.

This confirms configuration syntax/structure only; an actual Render deployment was not executed from this environment.

## Secret handling review — Passed for repository-level checks

- `.env` remains Git-ignored.
- `.streamlit/secrets.toml` remains Git-ignored.
- `.env.example` and `.streamlit/secrets.toml.example` contain placeholders only.
- hosted API keys are provided through `SecretStr` configuration.
- application health responses expose no secret values.

This is not a substitute for GitHub secret scanning/Gitleaks in the final hosted repository.

## Not tested in this build environment

- live Gemini API call (no user secret was requested or stored here);
- live Groq API call;
- actual Ollama/Qwen model inference;
- SQLGlot AST behavior at runtime;
- full LLM execution-match evaluation;
- semantic Sentence-Transformer model download/evaluation;
- Streamlit visual browser rendering;
- Docker image build/run;
- live Render deployment;
- live Streamlit Community Cloud deployment;
- GitHub Actions hosted execution;
- Ruff lint command (Ruff binary unavailable in this runtime).

These remain explicitly unverified rather than being represented as successful.
