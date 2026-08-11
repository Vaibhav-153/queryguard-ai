FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Tesseract is required only for scanned PDFs and image invoices.
# Normal text PDFs, DOCX and PPTX do not depend on OCR.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src

# Install the main backend together with optional OCR support.
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -e ".[ocr]"

COPY data ./data
COPY scripts ./scripts

RUN mkdir -p /tmp/queryguard-workspaces

EXPOSE 8000

# Render provides PORT dynamically.
# Local Docker falls back to port 8000.
CMD ["sh", "-c", "uvicorn queryguard.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]