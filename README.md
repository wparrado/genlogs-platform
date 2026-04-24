GenLogs — MVP

Overview

GenLogs is a minimal viable product (MVP) for visualizing and comparing logistics routes. It provides a React (Vite) frontend with an autocomplete cities input, route search, carrier filtering and a map visualization. The backend is a FastAPI service that serves city search, route search and metrics and persists data in Postgres for local development.

Key features (MVP)

- Cities autocomplete (typeahead)
- Search routes between origin and destination
- Compare carriers and route summaries
- Map visualization of routes (lazy-loaded to avoid bundler/runtime issues)

Architecture

A simple architecture for local development:

Frontend (Vite + React) -> Backend (FastAPI) -> Database (Postgres)
                             |
                             -> External map provider (Google Maps / Place IDs)

Mermaid (optional) - Architecture

```mermaid
flowchart LR
  U[User browser] -->|HTTP| F[Frontend]
  F -->|API| B[Backend]
  B -->|SQL| D[Postgres DB]
  B -->|HTTP| E[External Map Provider]
```

Data model (high level)

- City: id, name, place_id
- Route: id, origin_id, destination_id, summary, distance, duration
- Carrier: id, name
- RouteCarrier: route_id, carrier_id, price, transit_time

Mermaid ER diagram

```mermaid
erDiagram
  CITY {
    int id PK
    string name
    string place_id
  }
  ROUTE {
    int id PK
    int origin_id FK
    int destination_id FK
    string summary
    float distance
    float duration
  }
  CARRIER {
    int id PK
    string name
  }
  ROUTE_CARRIER {
    int route_id FK
    int carrier_id FK
    float price
    float transit_time
  }

  CITY ||--o{ ROUTE : has
  ROUTE ||--o{ ROUTE_CARRIER : offers
  CARRIER ||--o{ ROUTE_CARRIER : provides
```

Local development

Prerequisites

- Node.js (recommended LTS)
- npm or yarn
- Python 3.12+ (managed by the project's uv helper)
- Postgres (for full local backend; some endpoints may run with mock providers)

Frontend (run)

1. cd frontend
2. npm install
3. npm run dev
4. Open http://localhost:5173

Notes

- The frontend includes a Vite dev proxy configuration to forward `/api` requests to the backend at http://localhost:8000 (see frontend/vite.config.ts). This avoids CORS in development.
- The Map component is lazy-loaded (React.lazy + Suspense) to prevent runtime "require is not defined" errors when the ESM build is served.

Backend (run)

For development the project's uv helper is recommended. A minimal developer flow is:

1. cd backend
2. Synchronize the project environment (this will create/manage the virtualenv if needed):
   uv sync
3. Start the app using uv:
   uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
4. Health endpoint: http://127.0.0.1:8000/health

Notes:
- `uv sync` will prepare the virtualenv and install dependencies as configured for the project. Using the helper ensures a reproducible developer experience across machines.
- For edge cases you can still run the venv directly, but prefer the uv helper for consistency.

CORS and dev notes

- For development the backend is restricted to accept requests from http://localhost:5173 (configured in app.main). Production deployments should use environment-driven config and a narrower set of origins.
- If the Vite proxy is enabled, the frontend will call `/api/*` and the proxy will forward requests to the backend, avoiding CORS issues in the browser.

Database & seed

- Migrations are managed via Alembic (scripts exist under backend/). Run migrations before seeding.
- Example (project root):
  - PYTHONPATH=./backend/src uv run alembic -c backend/alembic.ini upgrade head
  - PYTHONPATH=./backend/src uv run python backend/scripts/seed_data.py

Testing

- Frontend unit tests: `cd frontend && npm test`
- Backend tests: run pytest in the backend package (uses the project's uv helper)

Contributing / Notes

- This README is a brief guide for the MVP. For production deployments, add environment-based configuration, stronger CORS policies, auth and secrets management.
- The map provider is abstracted behind provider modules (see backend/src/app/providers/maps). Replace or configure API keys as needed.

License

MIT
