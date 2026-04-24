"""GenLogs backend application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import health, search, cities, metrics

app = FastAPI(title="GenLogs API", version="0.1.0")

# Development-friendly CORS so the Vite dev server can call the API.
# Keep this narrow and only enable the local dev hosts; production should
# configure a stricter policy via environment/config.
# For local development allow all origins to simplify the dev flow. In
# production this should be set to a restricted list.
# Restrict CORS to the local Vite dev origin for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(search.router, prefix="/api")
app.include_router(cities.router, prefix="/api")
app.include_router(metrics.router, prefix="/api")
