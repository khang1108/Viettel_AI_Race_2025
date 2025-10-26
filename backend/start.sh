#!/usr/bin/env bash
set -e

echo "Starting application in ${ROLE:-api} mode..."

# Wait for Postgres
echo "Waiting for PostgreSQL..."
python - <<'PY'
import os, time, psycopg2
for i in range(60):
    try:
        psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB", "rag"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "postgres"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=int(os.getenv("POSTGRES_PORT", "5432"))
        ).close()
        print("PostgreSQL is ready!")
        break
    except Exception as e:
        if i % 10 == 0:
            print(f"Waiting for PostgreSQL... ({i}/60)")
        time.sleep(1)
else:
    raise SystemExit("PostgreSQL not reachable after 60 seconds")
PY

# Wait for RabbitMQ (only if worker)
if [ "${ROLE}" = "worker" ]; then
    echo "Waiting for RabbitMQ..."
    python - <<'PY'
import os, time, pika
for i in range(60):
    try:
        params = pika.ConnectionParameters(
            host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
            port=int(os.getenv("RABBITMQ_PORT", "5672")),
            credentials=pika.PlainCredentials(
                os.getenv("RABBITMQ_USER", "guest"),
                os.getenv("RABBITMQ_PASS", "guest")
            )
        )
        conn = pika.BlockingConnection(params)
        conn.close()
        print("RabbitMQ is ready!")
        break
    except Exception as e:
        if i % 10 == 0:
            print(f"Waiting for RabbitMQ... ({i}/60)")
        time.sleep(1)
else:
    raise SystemExit("RabbitMQ not reachable after 60 seconds")
PY
fi

# Apply schema idempotently (only for API service, not worker)
if [ "${ROLE}" != "worker" ]; then
    echo "Applying database schema..."
    PGPASSWORD="${POSTGRES_PASSWORD}" psql \
        -h "${POSTGRES_HOST}" \
        -p "${POSTGRES_PORT}" \
        -U "${POSTGRES_USER}" \
        -d "${POSTGRES_DB}" \
        -v ON_ERROR_STOP=1 \
        -f /app/app/db/schema.sql || echo "Schema already applied or error occurred (continuing...)"
fi

# Create data directories outside app folder
mkdir -p "${DATA_DIR:-/data}"
mkdir -p "${UPLOAD_DIR:-/data/uploads}"
mkdir -p "${SENTENCE_TRANSFORMERS_HOME:-/models}"

echo "Data directories:"
echo "  DATA_DIR: ${DATA_DIR:-/data}"
echo "  UPLOAD_DIR: ${UPLOAD_DIR:-/data/uploads}"
echo "  MODEL_CACHE: ${SENTENCE_TRANSFORMERS_HOME:-/models}"

# Start service based on role
if [ "${ROLE}" = "worker" ]; then
    echo "Starting Celery worker..."
    exec celery -A app.celery_app.celery_app worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=50
else
    echo "Starting FastAPI server..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload
fi