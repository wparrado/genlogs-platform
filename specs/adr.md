# Architecture Decision Records — GenLogs Platform

This document is the authoritative record of all significant architectural decisions made for the GenLogs MVP.
Every future change to the architecture, toolchain, or quality gates must be traceable to an entry here
or to a new ADR that supersedes one of the existing entries.

**AI systems and contributors must treat this file as a constraint boundary, not a suggestion.**
Before proposing any change that contradicts an accepted ADR, a new ADR must be written and accepted first.

---

## Index

| ID | Title | Status |
|---|---|---|
| ADR-001 | Python package manager: uv | Accepted |
| ADR-002 | Backend framework: FastAPI | Accepted |
| ADR-003 | Frontend framework: React + Vite | Accepted |
| ADR-004 | Frontend language: TypeScript | Accepted |
| ADR-005 | Frontend package manager: npm | Accepted |
| ADR-006 | Backend layered architecture | Accepted |
| ADR-007 | Frontend module boundary model | Accepted |
| ADR-008 | Backend architecture validation: archon-architecture | Accepted |
| ADR-009 | Frontend architecture validation: dependency-cruiser | Accepted |
| ADR-010 | Backend linting quality gate: pylint 10.00/10, no suppression | Accepted |
| ADR-011 | Pre-commit hooks as local quality gate | Accepted |
| ADR-012 | CI platform: GitHub Actions | Accepted |
| ADR-013 | Backend containerization: Docker for Google Cloud Run | Accepted |
| ADR-014 | Frontend deployment: static hosting (no SSR) | Accepted |
| ADR-015 | Configuration management: pydantic-settings + environment variables | Accepted |
| ADR-016 | Provider abstraction: primary (Google) + fallback (mock) | Accepted |
| ADR-017 | Outbound resilience: exponential retry (max 3) + circuit breaker on provider calls | Accepted |
| ADR-018 | Inbound rate limiting: 100 requests per minute per endpoint | Accepted |
| ADR-019 | Database engine: PostgreSQL 15 | Accepted |
| ADR-020 | In-memory cache: cachetools TTLCache for city and search queries | Accepted |

---

## ADR-001 — Python package manager: uv

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The backend requires dependency installation, virtual environment management, and a reproducible lock file.
Traditional `pip` with `requirements.txt` is fragile; `poetry` adds complexity. `uv` (Astral) offers
near-instant installs, a built-in lockfile (`uv.lock`), and full `pyproject.toml` compatibility.

### Decision
Use **uv** as the sole Python package manager for the GenLogs backend.
`pip` must not be used directly in CI, Dockerfiles, or local setup instructions; all installs go through `uv`.

### Consequences
- `pyproject.toml` remains the dependency manifest; `uv.lock` is committed to version control.
- CI uses `astral-sh/setup-uv` to bootstrap the tool.
- The Dockerfile uses `uv` to install dependencies before copying application code.
- Contributors must install `uv` locally before working on the backend.
- Any future introduction of `pip install` in scripts is a violation of this decision.

---

## ADR-002 — Backend framework: FastAPI

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The backend serves a single search API with input validation, provider orchestration, and structured JSON responses.
Flask lacks built-in validation and schema generation. Django is over-engineered for this scope.

### Decision
Use **FastAPI** with **Uvicorn** as the ASGI server.
Python version target is **3.12+**.

### Consequences
- All route definitions use FastAPI routers and Pydantic models for request/response validation.
- Async handlers are allowed but not required at the scaffold stage.
- The OpenAPI contract in `specs/search-api.openapi.yaml` is the source of truth;
  FastAPI's auto-generated docs must remain consistent with it.
- Switching frameworks requires a new ADR.

---

## ADR-003 — Frontend framework: React + Vite

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The frontend is a single-page application with a search form and result display.
No server-side rendering is needed. Next.js would add unnecessary complexity.
Create React App is deprecated. Vite provides fast HMR and a lean build pipeline.

### Decision
Use **React 18** with **Vite** as the build tool and development server.

### Consequences
- The application is a pure SPA; there is no server-side rendering or file-based routing.
- `vite.config.ts` is the authoritative build configuration.
- The frontend is built to static assets (`npm run build`) and served from a static host.
- Any introduction of SSR or a meta-framework (Next.js, Remix) requires a new ADR.

---

## ADR-004 — Frontend language: TypeScript

**Status:** Accepted  
**Date:** 2026-04-24

### Context
Type safety reduces integration bugs at the boundary between the frontend and the backend API contract.
TypeScript is the standard for production React projects.

### Decision
All frontend source files use **TypeScript** (strict mode enabled).
Plain JavaScript files must not be added to `frontend/src/`.

### Consequences
- `tsconfig.json` enables `strict: true`, `noUnusedLocals`, and `noUnusedParameters`.
- The TypeScript build check (`tsc --noEmit`) is part of CI and must pass.
- API response types must be typed; `any` assertions require justification.

---

## ADR-005 — Frontend package manager: npm

**Status:** Accepted  
**Date:** 2026-04-24

### Context
`bun` is faster but less battle-tested in CI environments and less familiar to reviewers.
For a technical test MVP, portability and reviewer compatibility outweigh raw speed.

### Decision
Use **npm** as the frontend package manager.
`bun`, `yarn`, and `pnpm` must not be introduced without a superseding ADR.

### Consequences
- `package-lock.json` is committed to version control.
- CI uses `npm ci` for reproducible installs.
- `npm run` scripts are the interface for all frontend automation tasks.

---

## ADR-006 — Backend layered architecture

**Status:** Accepted  
**Date:** 2026-04-24

### Context
Mixing HTTP routing, business logic, and external provider calls in the same module creates an unmaintainable codebase.
A clear layer hierarchy enforces separation of concerns and makes each layer independently testable.

### Decision
The backend follows a strict **four-layer architecture** inside `backend/src/app/`:

```
api/routes  →  services  →  providers  →  models
                    ↘               ↘
                    config          config
```

**Allowed dependencies (see also AT-007 to AT-011 in scaffold-spec.md):**

| Layer | May depend on |
|---|---|
| `api/routes` | `services`, `models`, `config` |
| `services` | `providers`, `models`, `config` |
| `providers` | `models`, `config` |
| `models` | *(nothing — no internal imports)* |
| `config` | *(nothing — no internal imports)* |

**Prohibited imports:**
- `services` must not import from `api/routes`.
- `providers` must not import from `api/routes` or `services`.
- `models` must not import from any other layer.
- `config` must not import from any other layer.

### Consequences
- Archon architecture tests (`tests/backend/test_architecture.py`) enforce these rules automatically.
- Any violation is detected by the pre-commit hook and CI before it enters the repository.
- Adding a new layer requires updating this ADR and the Archon test baseline together.

---

## ADR-007 — Frontend module boundary model

**Status:** Accepted  
**Date:** 2026-04-24

### Context
Without enforced import boundaries, React projects tend to develop circular dependencies and tight coupling
between feature logic, shared UI, and data-fetching code.

### Decision
The frontend enforces the following **three-layer import policy** inside `frontend/src/`:

```
features/search
    ↓           ↓
components    services/apiClient
```

**Allowed imports:**
- `features/search` may import from `components` and `services`.
- `components` may not import from `features`.
- `services` may not import from `components` or `features`.

**Prohibited imports (see AT-012 to AT-014 in scaffold-spec.md):**
- `services` importing UI layers (`components`, `features`).
- `components` importing feature internals (`features`).

### Consequences
- `dependency-cruiser` (`.dependency-cruiser.cjs`) enforces these rules.
- ESLint `import/no-restricted-paths` provides a fast local feedback layer.
- Any deliberate exception to these rules requires updating both this ADR and the cruiser config.

---

## ADR-008 — Backend architecture validation: archon-architecture

**Status:** Accepted  
**Date:** 2026-04-24

### Context
Manual code reviews cannot reliably catch layer violations at scale or under time pressure.
Automated architecture tests run on every commit and in CI without reviewer attention.

### Decision
Use **archon-architecture** with **pytest** for backend architecture validation.
Tests live in `tests/backend/test_architecture.py`.

### Consequences
- Architecture tests run in CI (backend job) and in the pre-commit hook.
- A failing architecture test blocks commits and CI.
- Tests cover both directory structure integrity and import boundary violations.
- Removing or skipping architecture tests requires a new ADR.

---

## ADR-009 — Frontend architecture validation: dependency-cruiser

**Status:** Accepted  
**Date:** 2026-04-24

### Context
JavaScript/TypeScript has no native import restriction mechanism.
`dependency-cruiser` provides a configurable, static-analysis-based rule engine for module boundaries.

### Decision
Use **dependency-cruiser** as the primary frontend architecture validation tool.
Configuration lives in `frontend/.dependency-cruiser.cjs`.
ESLint `import/no-restricted-paths` is used as a complementary fast-feedback layer.

### Consequences
- `npm run arch:validate` runs `depcruise` against `src/` on every commit (pre-commit hook) and in CI.
- A non-zero exit from `depcruise` blocks commits and CI.
- Rule changes require updating `.dependency-cruiser.cjs` and this ADR together.

---

## ADR-010 — Backend linting quality gate: pylint 10.00/10, no suppression

**Status:** Accepted  
**Date:** 2026-04-24

### Context
Partial lint scores allow silent quality degradation. Setting the threshold at 10.00/10 from the first commit
establishes an unambiguous baseline.

### Decision
The backend must achieve a **pylint score of 10.00/10**.
Achieving this score by suppressing rules via:
- inline `# pylint: disable` comments,
- `[tool.pylint."messages control"]` config-level ignores,
- or any other bypass mechanism

is **not permitted**. The code must be corrected to satisfy the rule.

The only acceptable exception is a third-party API signature that cannot be changed;
such suppressions require an explicit justification comment and must be reviewed before merging.

### Consequences
- The pylint gate runs in the pre-commit hook and CI.
- A score below 10.00/10 blocks commits and CI.
- Contributors must fix code, not silence warnings.
- Reviewers must reject PRs that introduce unjustified suppressions even if the CI score is 10.00/10.

---

## ADR-011 — Pre-commit hooks as local quality gate

**Status:** Accepted  
**Date:** 2026-04-24

### Context
CI catches errors after the fact. Pre-commit hooks give contributors immediate feedback before a commit
enters the history, reducing the cycle time for fixing quality issues.

### Decision
Use **pre-commit** with a package-root `.pre-commit-config.yaml`.
The following hooks are required and must not be removed:

| Hook | Blocks on |
|---|---|
| `backend-architecture-tests` | Archon test failure |
| `frontend-architecture-validation` | dependency-cruiser violation |
| `backend-pylint` | pylint score below 10.00/10 |

### Consequences
- Contributors must run `pre-commit install` after cloning the repository.
- The hook configuration must remain aligned with CI checks.
- Adding a hook does not require a new ADR; removing one does.

---

## ADR-012 — CI platform: GitHub Actions

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The repository is hosted on GitHub. GitHub Actions is the zero-friction CI choice for a GitHub-hosted project.

### Decision
Use **GitHub Actions** for CI/CD.
The workflow lives at `.github/workflows/ci.yml` and runs on `push` and `pull_request`.

The workflow has two jobs:
- `backend`: installs Python via uv, runs Archon tests, runs pylint gate.
- `frontend`: installs Node via npm, runs dependency-cruiser, runs TypeScript build check.

### Consequences
- CI must be green before any branch can be merged.
- The workflow is structured to allow new steps (tests, deploy) without redesigning the pipeline.
- Switching CI platforms requires a new ADR.

---

## ADR-013 — Backend containerization: Docker for Google Cloud Run

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The backend needs a portable, reproducible deployment artifact.
Google Cloud Run accepts Docker images directly and scales to zero when idle, making it cost-efficient for an MVP.

### Decision
The backend is packaged as a **Docker image** targeting **Google Cloud Run**.

Constraints:
- The image is based on `python:3.12-slim`.
- Secrets must not be baked into the image; they are injected as environment variables at runtime.
- The entrypoint is `uvicorn app.main:app --host 0.0.0.0 --port 8080` (Cloud Run default port).
- The `Dockerfile` lives at `backend/Dockerfile`.

### Consequences
- The image can be built and run locally without production secrets using the mock provider mode.
- Moving to a different runtime (Cloud Functions, App Engine, Kubernetes) requires a new ADR.
- The frontend is not containerized in the scaffold; see ADR-014.

---

## ADR-014 — Frontend deployment: static hosting (no SSR)

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The React SPA produces static assets after `npm run build`.
There is no server-side rendering requirement for the GenLogs MVP.
Static hosting (Firebase Hosting, Cloud Storage + CDN, or similar) is simpler and cheaper than containerized Node.

### Decision
The frontend is deployed as **static assets** to a static hosting provider.
No Node server, container, or SSR framework is required or permitted in the scaffold.
Firebase Hosting is the preferred target for Google Cloud alignment, but the decision is hosting-agnostic.

### Consequences
- The frontend build output (`dist/`) is the deployable artifact.
- The `VITE_API_BASE_URL` environment variable must be set at build time to point to the backend URL.
- Introducing SSR requires a new ADR and a Vite/framework change.

---

## ADR-015 — Configuration management: pydantic-settings + environment variables

**Status:** Accepted  
**Date:** 2026-04-24

### Context
Hardcoding configuration values creates security and portability risks.
A centralized, typed configuration object prevents scattered `os.getenv()` calls.

### Decision
All backend configuration is centralized in `backend/src/app/config/settings.py` using **pydantic-settings**.
Configuration is loaded from environment variables, with an optional `.env` file for local development.
The inner `Config` class pattern (Pydantic v1 style) must not be used; use `model_config = SettingsConfigDict(...)` instead.

Required settings and their defaults:

| Variable | Default | Purpose |
|---|---|---|
| `GENLOGS_ENV` | `development` | Runtime environment identifier |
| `GENLOGS_MAPS_PROVIDER` | `mock` | Active maps provider (`google` or `mock`) |
| `GENLOGS_GOOGLE_API_KEY` | `""` | Google Maps API key (empty in mock mode) |
| `GENLOGS_REQUEST_TIMEOUT_SECONDS` | `10` | Outbound HTTP timeout |

### Consequences
- The application runs locally without a real Google API key when `GENLOGS_MAPS_PROVIDER=mock`.
- Secrets are never committed to the repository; `.env` is in `.gitignore`.
- Adding a new config variable requires updating `settings.py` and this table.

---

## ADR-016 — Provider abstraction: primary (Google) + fallback (mock)

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The MVP must be demonstrable without a live Google Maps API key.
The business logic (carrier ranking) must be testable independently of the maps provider.

### Decision
The `providers` layer implements a **shared contract** (interface/protocol) with two concrete implementations:
1. **Google provider** — live city suggestions and route data via Google Maps API.
2. **Mock provider** — deterministic, hardcoded responses for local development and testing.

The active provider is selected at startup via `GENLOGS_MAPS_PROVIDER`.
Provider-specific errors are caught at the provider layer and mapped to shared application errors before
reaching `services` or `api/routes`.

### Consequences
- All tests can run without network access by using the mock provider.
- The Google provider implementation is isolated; replacing it with a different maps service only requires
  implementing the shared contract.
- Provider details (API keys, raw error messages) must not leak into the HTTP response.

---

## ADR-017 — Outbound resilience: exponential retry + circuit breaker on provider calls

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The `providers` layer makes outbound HTTP calls to Google Maps API.
Network failures, transient timeouts, and upstream throttling are expected in production.
Without a retry strategy the first transient error surfaces immediately to the user.
Without a circuit breaker, a sustained outage floods the upstream service with repeated failing calls
and keeps threads busy, degrading the backend under load.

### Decision
All outbound provider calls must implement:

1. **Exponential retry** — maximum **3 attempts** (1 initial call + 2 retries).
   Wait times follow exponential backoff: `1 s → 2 s` between attempts (base 2, starting at 1 s).
   Retry only on transient errors (network timeout, `502`, `503`, `504`).
   Do not retry on `400`, `401`, `403`, or `404` — these are not transient.

2. **Circuit breaker** — opens after **5 consecutive failures**, stays open for **30 seconds**.
   While open, calls fail immediately without hitting the upstream service.
   After the cool-down, one probe request is allowed (half-open state).

**Implementation libraries:**

| Concern | Library |
|---|---|
| Exponential retry | `tenacity` |
| Circuit breaker | `pybreaker` |

Both are added to backend runtime dependencies in `pyproject.toml`.

**Scope:** all classes in `backend/src/app/providers/` that make outbound HTTP calls.
The `services` and `api/routes` layers must not implement retry or circuit-breaker logic;
that responsibility belongs exclusively to the `providers` layer.

### Consequences
- Transient provider failures are absorbed by retry before the fallback provider is tried.
- A sustained provider outage stops sending traffic to the failing upstream quickly.
- The fallback (mock) provider is triggered when the primary provider's circuit is open or retries are exhausted.
- `tenacity` and `pybreaker` are added as runtime dependencies; tests must cover the retry path and the open-circuit path.
- Any change to retry count, backoff formula, or circuit-breaker thresholds requires updating this ADR.

---

## ADR-018 — Inbound rate limiting: 100 requests per minute per endpoint

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The MVP backend is a single-instance service without an API gateway.
Unbounded inbound traffic can exhaust provider quotas (Google Maps charges per request) and
overload the process under load. A per-endpoint rate limit protects both the backend and the upstream provider
without requiring infrastructure changes at the MVP stage.

### Decision
All public-facing endpoints (`GET /api/cities`, `GET /api/search`) must enforce a rate limit of
**100 requests per minute** per client IP address.

`GET /health` is exempt (used by health checks and monitoring).

**Implementation library:** `slowapi` (wraps the `limits` library; integrates natively with FastAPI/Starlette).

The limiter is initialized once in `backend/src/app/main.py` and applied as a decorator on each route handler.
The limit key is the client IP address extracted from the request.

Rate-limit responses return **HTTP 429 Too Many Requests** with a `Retry-After` header.

The limit value (`100/minute`) is defined as a constant in `backend/src/app/config/settings.py`
so it can be overridden via environment variable without code changes.

### Consequences
- Provider quota exhaustion from an abusive client is prevented at the application layer.
- `slowapi` is added to backend runtime dependencies in `pyproject.toml`.
- In-memory state is per-process; a multi-instance deployment requires a shared store (e.g., Redis).
  This is acceptable for the MVP single-instance scope and must be revisited before horizontal scaling.
- Tests must cover the `429` response path for both rate-limited endpoints.
- Any change to the limit, key strategy, or store backend requires updating this ADR.

---

## ADR-019 — Database engine: PostgreSQL 15

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The full GenLogs platform requires persistent storage for carrier reference data, city entities,
corridor statistics, camera captures, and regulatory enrichments (see `database-spec.md`).
The backend's `providers` layer needs access to carrier rankings and city reference data
to operate without depending exclusively on the Google Maps API for every request.

### Decision
Use **PostgreSQL 15** as the relational database engine.

Responsibilities in the backend:
- `providers` is the only layer that reads from or writes to the database.
  `services` and `api/routes` must not issue SQL queries directly.
- The database is accessed through the `providers` layer via a dedicated database provider
  that implements the same shared contract pattern as the Google Maps provider.

Tables relevant to the MVP search portal:
| Table | Purpose |
|---|---|
| `carriers` | Carrier names and identifiers for ranking |
| `city_reference` | Normalized city entities for fallback city lookup |
| `corridor_daily_stats` | Aggregate carrier activity per city pair |

Full schema is defined in `specs/database-spec.md`.

**Connection management:** a connection pool is configured via `GENLOGS_DATABASE_URL` in `settings.py`.
The database URL is never hardcoded; it is always injected via environment variable.

### Consequences
- `GENLOGS_DATABASE_URL` is added to `backend/src/app/config/settings.py` and the `.env.example`.
- An ORM or query builder (SQLAlchemy or asyncpg) is added to backend runtime dependencies.
- The `providers` boundary strictly owns all SQL; no raw queries appear in `services` or `api/routes`.
- Local development requires a running PostgreSQL instance (Docker Compose or local install).
- The database URL must not appear in committed files; `.env` is in `.gitignore`.
- Switching to a different relational engine requires a new ADR.

---

## ADR-020 — In-memory cache: cachetools TTLCache for city and search queries

**Status:** Accepted  
**Date:** 2026-04-24

### Context
City suggestion queries and route search queries for the same input are expensive:
they consume Google Maps API quota and add network latency.
In a typical search session, users repeat the same origin/destination pairs frequently.
An in-memory cache with a TTL absorbs repeated identical requests at zero cost without
requiring external infrastructure like Redis.

### Decision
Implement a **process-local in-memory TTL cache** in the `services` layer using `cachetools.TTLCache`.

**Cache is the responsibility of `services`, not `providers`.**
Providers are stateless data-access adapters; the decision of what to cache and for how long
is an orchestration concern that belongs to `services`.

**Two independent caches:**

| Cache | Key | TTL | Max entries | Env variable |
|---|---|---|---|---|
| City suggestions | `normalize(query)` — lowercased, stripped | 1 hour | 256 | `GENLOGS_CACHE_CITIES_TTL_SECONDS` |
| Search results | `(from_city_id, to_city_id)` | 15 minutes | 128 | `GENLOGS_CACHE_SEARCH_TTL_SECONDS` |

`GENLOGS_CACHE_MAX_SIZE` controls the maximum entries per cache instance (default `256`).
All three variables are defined in `backend/src/app/config/settings.py`.

**Cache flow:**
1. `services` checks the cache with the request key before calling `providers`.
2. On a **hit**, the cached result is returned immediately — no provider call is made.
3. On a **miss**, `services` calls `providers`, stores the result in the cache, then returns it.

**Implementation library:** `cachetools` — pure Python, no external dependencies, thread-safe with `@cached` decorator or explicit `TTLCache` instance.

### Consequences
- Repeated identical queries for the same city name or the same city pair do not consume Google Maps quota.
- Cache state is per-process and lost on restart; this is acceptable for an MVP with a single instance.
- A multi-instance deployment would require a shared cache (e.g., Redis); this must be revisited before horizontal scaling (see also ADR-018).
- `cachetools` is added to backend runtime dependencies in `pyproject.toml`.
- Tests must cover the cache hit path (no provider call) and the cache miss path (provider called and result stored).
- Changing TTL values does not require a new ADR; changing the cache strategy (e.g., moving to Redis) does.

---

## ADR-021 — Metrics: Prometheus instrumentation and exposure

**Status:** Accepted  
**Date:** 2026-04-24

### Context
The backend must observe provider behavior (Google Maps), DB queries, and other runtime signals to detect regressions, trigger alerts, and support operational diagnostics. During early development a JSON endpoint and in-memory counters were used for convenience, but they do not integrate with standard monitoring tooling.

### Decision
Adopt **Prometheus** as the primary metrics system for the GenLogs backend. The application will use the `prometheus_client` library to register counters and other metrics in a private CollectorRegistry and expose them via an HTTP endpoint. When the library is not available (local development or constrained environments) the application will fall back to an in-memory counter store and return JSON for the `/api/metrics` route.

### Consequences
- `prometheus_client` is added to runtime dependencies used in CI and staging. The code tolerates its absence for local/dev runs.
- A minimal set of counters is instrumented immediately: `maps_google_attempts`, `maps_google_failures`, `maps_google_circuit_open`, `db_get_carriers`. Additional metrics (histograms for provider latency, gauge for queue length) can be added iteratively.
- The metrics endpoint returns Prometheus exposition (`text/plain; version=0.0.4`) when `prometheus_client` is present; otherwise it returns a JSON mapping of known counters. A private CollectorRegistry is used to avoid global registry conflicts during tests and reuse.
- Tests can assert on the in-memory counters or call the Prometheus exposition when available. The CI job installs `prometheus-client` so integration environments expose Prometheus metrics.
- Operational implication: add Prometheus scrape job for the service in staging; configure alerting rules for high `maps_google_failures` or high error rates on search endpoints.

### Implementation
- Add a small metrics abstraction (`backend/src/app/metrics.py`) that exposes `inc(name)`, `get(name)`, `reset()` and `prometheus_metrics_latest()`.
- Instrument providers and DB provider calls to increment relevant counters.
- Expose `/api/metrics` via FastAPI which returns Prometheus exposition when available and JSON fallback otherwise.
- Ensure the CollectorRegistry is private to the application module to avoid collisions in unit tests.
- Add unit tests that exercise both the in-memory fallback and the Prometheus path by monkeypatching or installing `prometheus_client` in CI.

### Alternatives considered
- Keep the JSON-only approach (rejected — incompatible with standard monitoring platforms and alerts).  
- Use a Pushgateway pattern (rejected for MVP complexity and operation overhead).

### State and next steps
- Implementation completed in codebase: metrics abstraction, instrumentation and metrics endpoint with fallback.  
- Next operational steps: add Prometheus scrape configuration in staging; create simple alert rules for provider failures and high latency; consider exposing metrics at `/metrics` root if required by environment.

---

## How to update this document

1. Copy the template below.
2. Assign the next sequential ID.
3. Set **Status** to `Accepted`, `Deprecated`, or `Superseded by ADR-XXX`.
4. Commit the updated `adr.md` alongside the code change it documents.

### ADR template

```
## ADR-XXX — [Short title]

**Status:** Accepted | Deprecated | Superseded by ADR-XXX
**Date:** YYYY-MM-DD

### Context
[Why is this decision needed? What problem does it solve?]

### Decision
[What was decided? State it clearly and unambiguously.]

### Consequences
[What are the positive, negative, and neutral consequences of this decision?
What is now easier? What is now harder? What constraints does this impose?]
```
