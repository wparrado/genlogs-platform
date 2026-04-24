import threading
import time
import requests
import uvicorn

from app.main import app
from app.providers.db import init_db

# seed_data lives in backend/scripts; tests/conftest.py adds backend/ to sys.path
from scripts import seed_data


def _wait_for_server(url: str, timeout: int = 10) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.1)
    raise RuntimeError(f"Server at {url} did not become ready within {timeout}s")


def test_uvicorn_inprocess_runs_and_serves_requests():
    """Run uvicorn.Server in-process, ensure health and API endpoints respond.

    This test creates DB tables and seeds minimal data so it is self-contained
    for CI and local runs (requires Postgres available at configured URL).
    """
    # Ensure DB schema and seed data are present
    init_db()
    seed_data.seed()

    config = uvicorn.Config(app, host="127.0.0.1", port=8002, log_level="warning", lifespan="on")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    try:
        # Wait for server to be ready via health endpoint
        _wait_for_server("http://127.0.0.1:8002/health", timeout=15)

        # Health check
        r = requests.get("http://127.0.0.1:8002/health")
        assert r.status_code == 200
        assert r.json().get("status") == "ok"

        # Cities suggestion
        r = requests.get("http://127.0.0.1:8002/api/cities?query=New")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

        # Search (NY -> Washington)
        from_city = {"id": "mock:new_york", "label": "New York, NY, US", "city": "New York", "state": "NY", "country": "US"}
        to_city = {"id": "mock:washington", "label": "Washington, DC, US", "city": "Washington", "state": "DC", "country": "US"}
        r = requests.get("http://127.0.0.1:8002/api/search", params={"from_id": from_city["id"], "to_id": to_city["id"]})
        assert r.status_code == 200
        j = r.json()
        assert len(j.get("routes", [])) == 3
        assert len(j.get("carriers", [])) >= 3
    finally:
        # Signal server to exit and wait for thread to finish
        server.should_exit = True
        thread.join(timeout=5)
