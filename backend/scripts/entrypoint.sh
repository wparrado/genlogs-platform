#!/bin/sh
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${POSTGRES_USER:-genlogs}"
DB_PASSWORD="${DB_PASSWORD:-${POSTGRES_PASSWORD:-}}"
DB_NAME="${DB_NAME:-genlogs}"

# If GENLOGS_DATABASE_URL is not set, construct it from available DB_* env vars.
# Supports TCP host (host:port) and Unix socket path (e.g., /cloudsql/PROJECT:REGION:INSTANCE).
if [ -z "${GENLOGS_DATABASE_URL:-}" ]; then
  if printf '%s' "$DB_HOST" | grep -q '^/'; then
    # Unix socket connection string: host param points to socket directory
    GENLOGS_DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@/${DB_NAME}?host=${DB_HOST}"
  else
    GENLOGS_DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
  fi
  export GENLOGS_DATABASE_URL
fi

echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" >/dev/null 2>&1; do
  sleep 1
done

echo "Postgres is ready — starting app"
exec "$@"
