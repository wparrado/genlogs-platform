"""GenLogs backend application entry point."""
from fastapi import FastAPI
from app.api.routes import health, search

app = FastAPI(title="GenLogs API", version="0.1.0")

app.include_router(health.router)
app.include_router(search.router, prefix="/api")
