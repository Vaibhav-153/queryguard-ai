FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY data ./data
RUN pip install --upgrade pip && pip install .
RUN python scripts/setup_demo_db.py

EXPOSE 8000
CMD ["sh", "-c", "uvicorn queryguard.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
