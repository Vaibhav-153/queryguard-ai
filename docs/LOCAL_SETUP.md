# Local Setup Guide

## Supported baseline

- Windows 10/11, macOS, or Linux.
- Python 3.11+.
- Git.
- Optional Ollama for local AI.
- Optional Tesseract for scanned-document/image OCR.

## Windows PowerShell

```powershell
git clone https://github.com/Vaibhav-153/queryguard-ai.git
cd queryguard-ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[ui,dev]"
Copy-Item .env.example .env
python scripts/setup_chinook.py
queryguard-verify
pytest -v
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

## macOS/Linux

```bash
git clone https://github.com/Vaibhav-153/queryguard-ai.git
cd queryguard-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[ui,dev]"
cp .env.example .env
python scripts/setup_chinook.py
queryguard-verify
pytest -v
```

## Run in demo mode

`.env`:

```text
QUERYGUARD_LLM_PROVIDER=demo
```

Terminal 1:

```bash
uvicorn queryguard.api.main:app --reload
```

Terminal 2:

```bash
streamlit run app/streamlit_app.py
```

URLs:

```text
API docs: http://127.0.0.1:8000/docs
UI:       http://localhost:8501
```

## Add Ollama

Install Ollama using the official installer, then:

```bash
ollama pull qwen2.5-coder:7b
ollama list
```

`.env`:

```text
QUERYGUARD_LLM_PROVIDER=ollama
QUERYGUARD_OLLAMA_BASE_URL=http://localhost:11434
QUERYGUARD_OLLAMA_MODEL=qwen2.5-coder:7b
```

Restart FastAPI.

## Add Gemini

`.env`:

```text
QUERYGUARD_LLM_PROVIDER=gemini
QUERYGUARD_GEMINI_API_KEY=...
QUERYGUARD_GEMINI_MODEL=gemini-3.5-flash
```

Do not share or commit the key.

## Add Groq

```text
QUERYGUARD_LLM_PROVIDER=groq
QUERYGUARD_GROQ_API_KEY=...
QUERYGUARD_GROQ_MODEL=qwen/qwen3.6-27b
```

## Optional semantic retrieval

```bash
pip install -e ".[semantic]"
```

Then:

```text
QUERYGUARD_RETRIEVAL_STRATEGY=semantic
```

The first run may download the embedding model.

## Optional OCR

Python wrapper:

```bash
pip install -e ".[ocr]"
```

You must also install the **Tesseract system binary** and ensure `tesseract` is on `PATH`.

Verify:

```bash
tesseract --version
```

Without Tesseract, normal text PDFs still work; scanned pages/images return a clear OCR dependency message.

## Docker

Demo mode:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000/docs
http://localhost:8501
```

Stop:

```bash
docker compose down
```

For Ollama running on the host, Docker uses `host.docker.internal` through the compose environment default.

## Clean restart

Temporary user workspaces live under:

```text
data/workspaces/
```

They are Git-ignored. To remove local workspaces manually, delete child folders while keeping `.gitkeep`.
