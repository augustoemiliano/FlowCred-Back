#!/bin/sh
set -e
mkdir -p /app/data
mkdir -p "${UPLOAD_DIR:-/app/uploads}"
alembic upgrade head
if [ -n "${INITIAL_ADMIN_USERNAME:-}" ] && [ -n "${INITIAL_ADMIN_PASSWORD:-}" ]; then
  python -m app.scripts.ensure_admin
fi
python -m app.scripts.seed_dev_demo
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
