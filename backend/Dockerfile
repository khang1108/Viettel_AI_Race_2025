# backend/Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

# initialize DB schema at container start (idempotent)
COPY backend/app/db/schema.sql /docker-entrypoint-initdb.d/schema.sql
# Not executed automatically here; we’ll run it via a tiny startup script:
COPY backend/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
