#!/usr/bin/env bash
set -euo pipefail

# Script to start Postgres in Docker, wait for readiness, run Alembic migrations and seed data.
# Run from repository root: bash genlogs_platform/backend/scripts/run_migrations_local.sh

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

echo "Starting postgres container via docker-compose..."
docker-compose up -d db

echo "Waiting for Postgres to become ready (pg_isready inside container)..."
# Use docker-compose exec -T to avoid TTY issues in CI/envs without a TTY
until docker-compose exec -T db pg_isready -U genlogs >/dev/null 2>&1; do
  printf "."
  sleep 1
done

echo "\nPostgres is ready. Running Alembic migrations..."
PYTHONPATH=./backend/src uv run alembic -c backend/alembic.ini upgrade head

echo "Seeding database with minimal data..."
PYTHONPATH=./backend/src uv run python backend/scripts/seed_data.py

echo "Migrations and seed complete."
