# Deployment guide

For the recruiter-facing cloud deployment, follow [`CLOUD_DEPLOYMENT.md`](CLOUD_DEPLOYMENT.md).

## Supported modes

| Mode | Provider | Secret required | Best use |
|---|---|---|---|
| Offline smoke | `demo` | No | CI and pipeline checks |
| Local AI | `ollama` | No | local/private inference |
| Hosted default | `gemini` | Gemini API key | public portfolio preview |
| Hosted alternative | `groq` | Groq API key | free-plan/open-model alternative |

## Local installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[ui,dev]"
python scripts/setup_chinook.py
cp .env.example .env
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Run API

```bash
uvicorn queryguard.api.main:app --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

## Run UI

```bash
QUERYGUARD_API_URL=http://localhost:8000 streamlit run app/streamlit_app.py
```

## Provider variables

### Ollama

```text
QUERYGUARD_LLM_PROVIDER=ollama
QUERYGUARD_OLLAMA_BASE_URL=http://localhost:11434
QUERYGUARD_OLLAMA_MODEL=qwen2.5-coder:7b
```

### Gemini

```text
QUERYGUARD_LLM_PROVIDER=gemini
QUERYGUARD_GEMINI_API_KEY=<secret>
QUERYGUARD_GEMINI_MODEL=gemini-3.5-flash
QUERYGUARD_GEMINI_THINKING_LEVEL=low
```

### Groq

```text
QUERYGUARD_LLM_PROVIDER=groq
QUERYGUARD_GROQ_API_KEY=<secret>
QUERYGUARD_GROQ_MODEL=qwen/qwen3.6-27b
```

## API protection

If `QUERYGUARD_API_ACCESS_KEY` is set, `/query` requires:

```text
X-QueryGuard-Key: <same secret>
```

The `/health` and `/schema` endpoints remain public for portfolio inspection of the sample Chinook deployment.

## Render port support

The `queryguard-api` console command reads the standard `PORT` environment variable. `render.yaml` also starts Uvicorn with `$PORT`, so the backend binds correctly on Render.

## Docker

```bash
docker compose up --build
```

Compose defaults to the deterministic demo provider. To use a real provider, pass the matching environment variables before starting Compose.

## Production boundary

This repository is suitable for a portfolio preview. A real enterprise deployment still needs user authentication, authorization, per-user quotas, audited access policy, production database roles, monitoring, durable rate limiting, private network design, and a deployment-specific threat review.
