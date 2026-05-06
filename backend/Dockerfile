FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy source early so the build step (uv sync) can build the package
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY pyproject.toml uv.lock alembic.ini ./
RUN uv sync --no-dev --frozen

# Install postgres client for pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Copy entrypoint and make executable
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Place application code where runtime expects it
COPY src/ ./app/

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
