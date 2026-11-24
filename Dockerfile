FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# System libraries WeasyPrint needs to render receipts and invoices.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Collect static files at build time (the key is only used for this step).
RUN SECRET_KEY=build-only-not-secret python manage.py collectstatic --noinput

# SQLite lives in /app/data so it can be mounted as a volume. Ignored when
# PostgreSQL (DB_HOST) is configured.
ENV SQLITE_PATH=/app/data/db.sqlite3
RUN useradd --create-home --uid 1000 app && mkdir -p /app/data && chown -R app:app /app
VOLUME ["/app/data"]
USER app

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn InventoryMS.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3} --timeout 60 --access-logfile -"]
