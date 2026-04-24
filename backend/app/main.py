"""GenLogs backend application entry point."""
from fastapi import FastAPI
from app.api.routes import health, search, cities, metrics

app = FastAPI(title="GenLogs API", version="0.1.0")

app.include_router(health.router)
app.include_router(search.router, prefix="/api")
app.include_router(cities.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
