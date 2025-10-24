#!/usr/bin/env bash
set -e

# wait for Postgres
python - <<'PY'
import os, time, psycopg2
for _ in range(60):
    try:
        psycopg2.connect(
            dbname=os.getenv("PGDATABASE"),
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            host=os.getenv("PGHOST"),
            port=os.getenv("PGPORT")
        ).close()
        break
    except Exception:
        time.sleep(1)
else:
    raise SystemExit("DB not reachable")
PY

# apply schema idempotently
psql "postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${PGDATABASE}" \
  -v ON_ERROR_STOP=1 -f /app/app/db/schema.sql || true

# decide role by env
if [ "${ROLE}" = "worker" ]; then
  exec celery -A app.celery_app.celery_app worker -l info
else
  exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
