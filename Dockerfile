FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATABASE_PATH=/app/data/listings.sqlite3

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p /app/data && chown -R app:app /app

USER app

VOLUME ["/app/data"]

HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import os, pathlib; p=pathlib.Path(os.environ.get('DATABASE_PATH', '/app/data/listings.sqlite3')); raise SystemExit(0 if p.parent.exists() else 1)"

CMD ["python", "main.py"]
