#!/usr/bin/env sh
# Render / container entrypoint — respects $PORT (default 8000).
set -eu

PORT="${PORT:-${API_PORT:-8000}}"
HOST="${API_HOST:-0.0.0.0}"
WORKERS="${WEB_CONCURRENCY:-1}"

echo "Starting EDP API on ${HOST}:${PORT} (workers=${WORKERS})"

if [ "${WORKERS}" -gt 1 ]; then
  exec uvicorn app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --proxy-headers \
    --forwarded-allow-ips='*' \
    --timeout-keep-alive 5 \
    --timeout-graceful-shutdown 30
else
  exec uvicorn app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --proxy-headers \
    --forwarded-allow-ips='*' \
    --timeout-keep-alive 5 \
    --timeout-graceful-shutdown 30
fi
