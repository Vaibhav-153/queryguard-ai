# Project manifest

QueryGuard AI cloud-preview edition

- Version: 1.1.0
- Build date: 2026-08-10
- Packaged project files: 92
- Default hosted LLM: Gemini 3.5 Flash
- Optional hosted LLM: Groq / Qwen 3.6 27B
- Local/offline LLM: Ollama (Qwen2.5-Coder 7B default)
- Demo database: Chinook 1.4.5 SQLite
- Hosted backend: Render Blueprint (`render.yaml`)
- Hosted frontend: Streamlit Community Cloud

## Verification snapshot

- Python compilation: Passed.
- Executed tests: 17 passed.
- SQLGlot-dependent modules: 3 skipped in the artifact runtime because SQLGlot could not be installed there.
- Lexical table retrieval: Recall@1 0.800; Recall@3 0.967; Recall@5 0.967 on 15 custom Chinook questions.
- Render YAML structure: Parsed and validated.
- Obvious Gemini/Groq live-key prefix scan: No keys found.
- Live Gemini/Groq/Ollama inference: Not tested in the artifact environment.

See `reports/BUILD_VERIFICATION.md` for the exact tested/not-tested boundary.

## File counts by top-level area

- `(root)`: 15
- `.github`: 1
- `.streamlit`: 2
- `app`: 1
- `artifacts`: 1
- `assets`: 1
- `configs`: 2
- `data`: 6
- `docs`: 8
- `logs`: 1
- `reports`: 1
- `results`: 4
- `scripts`: 4
- `src`: 35
- `tests`: 10

## Important deployment files

- `render.yaml` — Render FastAPI Blueprint.
- `requirements.txt` — Streamlit Community Cloud dependency entrypoint.
- `.streamlit/config.toml` — hosted Streamlit settings.
- `.streamlit/secrets.toml.example` — safe secret template; real file is Git-ignored.
- `.env.example` — provider/configuration template; real `.env` is Git-ignored.
- `docs/CLOUD_DEPLOYMENT.md` — exact cloud deployment workflow.
- `SECURITY.md` — preview security boundary and known gaps.
