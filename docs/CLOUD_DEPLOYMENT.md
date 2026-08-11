# Cloud Deployment — Render API + Streamlit Community Cloud

This deployment is intended for a public portfolio demo using public/non-sensitive data.

## Architecture

```text
Browser
  ↓
Streamlit Community Cloud
  ↓ HTTPS + QUERYGUARD_API_ACCESS_KEY
Render FastAPI
  ↓ private QUERYGUARD_GEMINI_API_KEY
Gemini API
```

## 1. GitHub

Push the repository without `.env` or `.streamlit/secrets.toml`.

The repository already contains:

```text
render.yaml
requirements.txt
app/streamlit_app.py
```

## 2. Gemini key

Create a key in Google AI Studio.

Do not paste the real key into GitHub or Streamlit secrets. It belongs on Render only.

## 3. Render Blueprint

Create **New → Blueprint** and select this repository.

`render.yaml` configures:

- Python web service;
- `pip install -e .`;
- Uvicorn binding to `$PORT`;
- `/health` health check;
- Gemini provider;
- lexical retrieval;
- temporary `/tmp/queryguard-workspaces`;
- 25 MB per-file, 50 MB combined, 8-file hosted upload limits.

Render asks for two unsynced values:

```text
QUERYGUARD_GEMINI_API_KEY
QUERYGUARD_API_ACCESS_KEY
```

Choose a long random value for `QUERYGUARD_API_ACCESS_KEY`. Enter the raw value without quote characters in Render.

## 4. Test backend

Open:

```text
https://<render-service>.onrender.com/health
```

Expected shape:

```json
{
  "status": "ok",
  "database_available": true,
  "llm_provider": "gemini",
  "api_protected": true
}
```

`/health` is public; query/upload endpoints can require the shared key.

## 5. Streamlit Community Cloud

Create an app using:

```text
Repository: Vaibhav-153/queryguard-ai
Branch: main
Main file: app/streamlit_app.py
```

Add secrets:

```toml
QUERYGUARD_API_URL = "https://<render-service>.onrender.com"
QUERYGUARD_API_ACCESS_KEY = "the-exact-same-value-used-on-render"
```

Do not put the Gemini key here.

After changing Streamlit secrets, reboot the app. After changing Render environment variables, save/deploy the service.

## Common key mismatch

Render value:

```text
abc123
```

Streamlit TOML:

```toml
QUERYGUARD_API_ACCESS_KEY = "abc123"
```

The quotes in TOML are syntax. In Render, do not enter literal quote characters.

## Hosted limitations

- free/low-cost services may sleep or change limits;
- temporary uploads can disappear on service restart;
- OCR system binaries are not installed by the simple Render blueprint;
- semantic retrieval may be too memory-heavy for a small free instance;
- public hosted use should be limited to demonstration/non-sensitive data.

For private files, local Ollama is the recommended architecture.
## Free-hosting constraints (verified 2026-08-11)

Render's official Free service documentation currently states that a Free web service:

- uses a `512 MB RAM / 0.1 CPU` instance;
- spins down after 15 minutes without inbound traffic;
- can take roughly a minute to spin back up;
- receives 750 Free instance hours per workspace per calendar month;
- uses an ephemeral filesystem, so uploaded workspaces disappear on spin-down/restart/redeploy.

That behavior is acceptable here because uploads are intentionally temporary. It is **not** appropriate for durable user storage.

Official source:

```text
https://render.com/docs/free
```

Streamlit Community Cloud also has resource limits. QueryGuard keeps the frontend lightweight and sets `.streamlit/config.toml` to a 50 MB frontend upload limit, while the backend applies its own stricter per-file/combined/count checks. Streamlit documents a 200 MB `st.file_uploader` default before configuration; QueryGuard intentionally uses a smaller project limit.

Official source:

```text
https://docs.streamlit.io/knowledge-base/deploy/increase-file-uploader-limit-streamlit-cloud
```

