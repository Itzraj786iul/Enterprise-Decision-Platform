#!/usr/bin/env bash
# Smoke-check local health endpoints (foundation).
set -euo pipefail

echo "Checking backend /health ..."
curl -fsS "http://localhost:8000/health" | tee /dev/stderr
echo

echo "Checking frontend /api/health ..."
curl -fsS "http://localhost:3000/api/health" | tee /dev/stderr
echo

echo "OK"
