FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# OCR is optional outside Docker, but the API image includes Tesseract so
# scanned PDF/image invoice workflows work in the reproducible container path.
RUN apt-get update && \
    apt-get install -y --no-install-recommends tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir --upgrade pip && \
    python -m pip install --no-cache-dir -e ".[ocr]"

COPY data ./data
COPY scripts ./scripts

RUN mkdir -p /app/data/workspaces

EXPOSE 8000
CMD ["uvicorn", "queryguard.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
