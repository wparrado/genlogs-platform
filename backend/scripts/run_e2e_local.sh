#!/usr/bin/env bash
set -euo pipefail

# Start DB, migrate, seed, start uvicorn and run e2e tests, then teardown.
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo "Starting postgres via docker-compose..."
docker-compose up -d db

echo "Waiting for postgres..."
until docker-compose exec -T db pg_isready -U genlogs >/dev/null 2>&1; do
  printf "."
  sleep 1
done

echo "\nRunning migrations..."
PYTHONPATH=./backend/src uv run alembic -c backend/alembic.ini upgrade head

echo "Seeding data..."
PYTHONPATH=./backend/src uv run python backend/scripts/seed_data.py

# Start uvicorn on port 8001 and write PID
echo "Starting uvicorn on :8001"
PYTHONPATH=./backend/src uv run uvicorn app.main:app --host 127.0.0.1 --port 8001 --log-level warning &
SERVER_PID=$!
echo $SERVER_PID > /tmp/genlogs_uvicorn.pid

# Wait for health
echo "Waiting for app health..."
until curl -sS http://127.0.0.1:8001/health >/dev/null 2>&1; do
  printf "."
  sleep 1
done

echo "Running E2E pytest..."
PYTHONPATH=./backend/src uv run pytest backend/tests/functional_e2e -q

TEST_STATUS=$?

# Teardown
echo "Killing server (pid $SERVER_PID)"
kill $SERVER_PID || true
sleep 1

echo "Stopping postgres..."
docker-compose down -v

exit $TEST_STATUS
