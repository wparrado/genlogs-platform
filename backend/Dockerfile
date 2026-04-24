FROM python:3.12-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy source early so the build step (uv sync) can build the package
COPY src/ ./src/
COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev --frozen

# Place application code where runtime expects it
COPY src/ ./app/

EXPOSE 8080

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
