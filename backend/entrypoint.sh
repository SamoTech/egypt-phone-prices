#!/bin/sh
set -e

echo "SERVICE_TYPE=${SERVICE_TYPE}"

if [ "$SERVICE_TYPE" = "worker" ]; then
  echo "Starting Celery worker + beat..."
  exec celery -A app.tasks.celery_app worker \
    --beat \
    --scheduler celery.beat.PersistentScheduler \
    --loglevel=info \
    --concurrency=2
else
  echo "Starting FastAPI..."
  exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers 2
fi
