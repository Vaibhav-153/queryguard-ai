# Deployment Overview

QueryGuard supports three practical execution styles. Detailed commands live in `LOCAL_SETUP.md` and `CLOUD_DEPLOYMENT.md`.

## 1. Local Python

Best for learning and development.

```text
Streamlit -> localhost FastAPI -> Demo/Ollama/Gemini/Groq -> local workspaces
```

Install:

```bash
python -m venv .venv
# activate the environment
python -m pip install --upgrade pip
pip install -e ".[ui,dev]"
python scripts/setup_chinook.py
```

Run API:

```bash
uvicorn queryguard.api.main:app --reload
```

Run UI in a second terminal:

```bash
streamlit run app/streamlit_app.py
```

## 2. Local Docker Compose

Best for a reproducible two-container demonstration.

```bash
docker compose up --build
```

The API image includes Tesseract + the Python OCR adapter so scanned PDF/image invoice workflows can run in the container path. The default provider is `demo`; set provider environment variables before Compose when using Ollama/Gemini/Groq.

## 3. Hosted portfolio preview

```text
Browser
  -> Streamlit Community Cloud
  -> HTTPS + X-QueryGuard-Key
  -> Render FastAPI
  -> Gemini (default hosted provider)
  -> temporary /tmp workspaces
```

The public preview intentionally uses smaller upload limits and lexical retrieval to keep the backend lightweight. Render's ephemeral filesystem means uploaded workspaces are temporary and can disappear on restart/redeploy; that is acceptable for the portfolio workflow and is not presented as durable storage.

## Provider modes

| Provider | Network required? | Secret | Intended use |
|---|---:|---|---|
| `demo` | No | none | deterministic Chinook/CI smoke checks |
| `ollama` | only local Ollama HTTP | none | private/local AI |
| `gemini` | Yes | Gemini API key | hosted demo |
| `groq` | Yes | Groq API key | optional hosted alternative |

## API access control

Set the same private value on the API and UI:

```text
QUERYGUARD_API_ACCESS_KEY=<random private value>
```

The UI sends it in `X-QueryGuard-Key`. The value must never be committed to GitHub.

## Production boundary

A real multi-user product would need authenticated users, per-user authorization/quotas, durable encrypted storage, malware scanning, production database roles, centralized monitoring/audit logs, and a deployment-specific threat review.
