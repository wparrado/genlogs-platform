# Architecture specification

## Architectural intent
The MVP should stay simple, implementation-friendly, and easy to demo. A lightweight layered architecture is enough for the requested scope.

## Data flow diagrams

### City suggestion flow
Triggered when the user types in the origin or destination field.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant SPA as React SPA
    participant RL as Rate Limiter<br/>(slowapi)
    participant Routes as api/routes
    participant Services as services
    participant Cache as In-memory Cache<br/>(cachetools TTLCache)
    participant Providers as providers
    participant CB as Circuit Breaker<br/>(pybreaker)
    participant Google as Google Maps API
    participant DB as PostgreSQL

    User->>SPA: Types city name
    SPA->>RL: GET /api/cities?q=...
    RL-->>SPA: 429 Too Many Requests (if limit exceeded)
    RL->>Routes: Request passes
    Routes->>Services: get_city_suggestions(query)
    Services->>Cache: Lookup key = normalize(query)

    alt Cache HIT (TTL not expired)
        Cache-->>Services: Cached CitySuggestion[]
        Services-->>Routes: CitySuggestion[] (from cache)
    else Cache MISS
        Services->>Providers: suggest_cities(query)
        Providers->>CB: Check circuit state

        alt Circuit CLOSED (healthy)
            CB->>Google: Autocomplete request
            Google-->>CB: City suggestions
            CB-->>Providers: City suggestions
        else Circuit OPEN (upstream failing)
            CB-->>Providers: Fail fast (no network call)
            Providers->>DB: Read city_reference fallback
            DB-->>Providers: Stored city entities
        end

        Providers-->>Services: Normalized CitySuggestion[]
        Services->>Cache: Store key=normalize(query), TTL=1 hour
        Services-->>Routes: CitySuggestion[]
    end

    Routes-->>SPA: 200 JSON suggestions
    SPA-->>User: Renders dropdown list
```

### Route search flow
Triggered when the user submits the search form with origin and destination selected.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant SPA as React SPA
    participant RL as Rate Limiter<br/>(slowapi)
    participant Routes as api/routes
    participant Services as services
    participant Cache as In-memory Cache<br/>(cachetools TTLCache)
    participant Providers as providers
    participant CB as Circuit Breaker<br/>(pybreaker)
    participant Google as Google Maps API
    participant DB as PostgreSQL

    User->>SPA: Submits search (from, to)
    SPA->>RL: GET /api/search
    RL-->>SPA: 429 Too Many Requests (if limit exceeded)
    RL->>Routes: Request passes

    Routes->>Routes: Validate request payload
    Routes->>Services: search_routes(from, to)
    Services->>Cache: Lookup key = (from_city_id, to_city_id)

    alt Cache HIT (TTL not expired)
        Cache-->>Services: Cached SearchResponse
        Services-->>Routes: SearchResponse (from cache)
    else Cache MISS
        par Fetch route data
            Services->>Providers: get_routes(from, to)
            Providers->>CB: Check circuit state

            alt Circuit CLOSED — attempt 1..3 with exponential backoff
                CB->>Google: Directions / Distance Matrix
                Google-->>CB: Route data
                CB-->>Providers: Route distance and duration
            else All retries exhausted or Circuit OPEN
                Providers-->>Services: ProviderError (fallback triggered)
            end

        and Fetch carrier reference data
            Services->>Providers: get_carriers(from, to)
            Providers->>DB: SELECT from carriers + corridor_daily_stats
            DB-->>Providers: Carrier rows for city pair
            Providers-->>Services: Carrier[]
        end

        Services->>Services: Apply carrier ranking rules
        Services->>Cache: Store key=(from_city_id, to_city_id), TTL=15 min
        Services-->>Routes: SearchResponse(routes, carriers)
    end

    Routes-->>SPA: 200 JSON SearchResponse
    SPA-->>User: Renders routes and ranked carrier list
```
    Routes-->>SPA: 200 JSON SearchResponse
    SPA-->>User: Renders routes and ranked carrier list
```

### Error and resilience flow
Shows how provider failures and circuit-breaker state changes are handled.

```mermaid
sequenceDiagram
    autonumber
    participant Providers as providers
    participant CB as Circuit Breaker<br/>(pybreaker)
    participant Retry as Retry policy<br/>(tenacity)
    participant Google as Google Maps API
    participant DB as PostgreSQL
    participant Services as services

    Providers->>CB: Call primary provider
    CB->>Retry: Execute with retry policy

    loop Up to 3 attempts
        Retry->>Google: HTTP request
        alt Transient error (502 / 503 / timeout)
            Google-->>Retry: Error response
            Retry->>Retry: Wait (1s, then 2s) and retry
        else Success
            Google-->>Retry: 200 OK
            Retry-->>CB: Result
            CB-->>Providers: Result
        end
    end

    alt All retries exhausted → CB records failure
        CB->>CB: Increment failure counter
        alt Failure count >= 5 → circuit opens
            CB-->>Providers: CircuitBreakerError (circuit OPEN)
            Providers->>DB: Fallback — read stored data
            DB-->>Providers: Fallback result
        else Failure count < 5
            CB-->>Providers: Last error propagated
        end
        Providers-->>Services: ProviderError with fallback result or error detail
    end
```

## C4 diagrams

### Level 1 — System context
Shows GenLogs in relation to its users and external systems.

```mermaid
C4Context
    title System Context — GenLogs

    Person(user, "Freight User", "Searches for freight routes and carrier options between cities")
    System(genlogs, "GenLogs Platform", "Freight logistics search portal: suggests cities, retrieves routes, and ranks carriers")
    System_Ext(googlemaps, "Google Maps API", "Provides city autocomplete suggestions and route distance/duration data")

    Rel(user, genlogs, "Searches routes and carrier options", "HTTPS")
    Rel(genlogs, googlemaps, "City suggestions and route lookup", "HTTPS / REST")
```

### Level 2 — Container diagram
Shows all runtime containers and how they communicate.

```mermaid
C4Container
    title Container Diagram — GenLogs

    Person(user, "Freight User")

    Container(spa, "React SPA", "React 18 · Vite · TypeScript", "Single-page freight search interface running in the browser. Collects user input, renders route and carrier results.")
    Container(api, "FastAPI Backend", "Python 3.12 · FastAPI · Uvicorn · uv", "REST API. Validates requests, orchestrates carrier ranking logic, and delegates provider calls.")
    ContainerDb(db, "PostgreSQL", "PostgreSQL 15", "city_reference (autocomplete fallback), carriers (master data), carrier_routes (ranking rules per city pair).")
    System_Ext(googlemaps, "Google Maps API", "City autocomplete suggestions and route distance/duration data")

    Rel(user, spa, "Uses", "HTTPS")
    Rel(spa, api, "City lookup and route search", "HTTPS / JSON")
    Rel(api, googlemaps, "City and route queries", "HTTPS / REST · Circuit Breaker + Retry")
    Rel(api, db, "Reads carrier and city reference data", "TCP / SQL")
```

### Level 3 — Backend component diagram
Shows the internal layers of the FastAPI backend and their external dependencies.

```mermaid
C4Component
    title Component Diagram — FastAPI Backend

    Container_Boundary(backend, "FastAPI Backend") {
        Component(routes, "api/routes", "FastAPI routers", "HTTP endpoints: GET /health, GET /api/cities, GET /api/search. Input validation, rate limiting (100 req/min), and response serialization.")
        Component(services, "services", "Python modules", "Business logic: carrier ranking, normalization, orchestration. Owns in-memory cache (TTLCache). No HTTP concerns.")
        Component(cache, "In-memory Cache", "cachetools TTLCache", "Cities cache: key=normalized_query, TTL=1 hour, max 256 entries. Search cache: key=(from_id, to_id), TTL=15 min, max 128 entries.")
        Component(providers, "providers", "Python modules", "External data abstraction: Google Maps provider (primary), mock provider (fallback), and database provider. Applies circuit breaker + exponential retry on outbound calls.")
        Component(models, "models", "Pydantic models", "Shared domain entities and DTOs used across all layers.")
        Component(config, "config/settings", "pydantic-settings · uv", "Centralized environment configuration loaded from env vars or .env file.")
    }

    System_Ext(googlemaps, "Google Maps API", "City suggestions and route data")
    ContainerDb_Ext(db, "PostgreSQL", "city_reference, carriers, carrier_routes")

    Rel(routes, services, "Delegates business logic to")
    Rel(routes, models, "Validates and serializes with")
    Rel(routes, config, "Reads rate limit and settings from")
    Rel(services, cache, "Reads from / writes to")
    Rel(services, providers, "Calls on cache MISS")
    Rel(services, models, "Operates on")
    Rel(services, config, "Reads TTL and cache settings from")
    Rel(providers, models, "Returns normalized")
    Rel(providers, config, "Reads API keys and timeouts from")
    Rel(providers, googlemaps, "City and route queries", "HTTPS · Circuit Breaker + Retry")
    Rel(providers, db, "Reads carrier and city reference data", "SQL")
```

### Level 3 — Frontend component diagram
Shows the internal layers of the React SPA.

```mermaid
C4Component
    title Component Diagram — React SPA

    Container_Boundary(spa, "React SPA") {
        Component(app, "App", "React component", "Application shell. Top-level layout and section placeholders.")
        Component(search, "features/search", "React feature module", "Search form, result display, and user interaction. Orchestrates components and service calls.")
        Component(components, "components", "React UI components", "Shared presentational components reused across features. No feature-specific logic.")
        Component(apiclient, "services/apiClient", "TypeScript module", "HTTP client wrapping fetch. Abstracts the backend base URL and request/response cycle.")
    }

    Rel(app, search, "Renders")
    Rel(search, components, "Composes shared UI from")
    Rel(search, apiclient, "Fetches data via")
```

## High-level modules
1. **Frontend SPA**
   - React single-page client
   - Search form, route results, carrier results, and error states
2. **Backend API**
   - FastAPI application
   - Request validation, orchestration, and shared error mapping
3. **Carrier service**
   - Deterministic ranking logic based on canonical city pairs
4. **Maps provider layer**
   - Primary provider: Google-backed city lookup and route lookup
   - Secondary provider: fallback implementation with the same contract
5. **Shared contracts**
   - DTOs and API schemas used by both implementation and tests

## Proposed runtime layout
```text
Browser
  -> React SPA
     -> FastAPI API
        -> CarrierService
        -> MapsProvider (Google primary, fallback secondary)
```

## Information flow
### City suggestion flow
1. The frontend sends the current search text to `GET /api/cities`.
2. The backend validates the query.
3. The backend asks the active maps provider for city suggestions.
4. The provider response is normalized into the shared `CitySuggestion` contract.
5. The backend returns normalized suggestions to the frontend.

### Route search flow
1. The frontend submits the selected `from` and `to` cities to `GET /api/search`.
2. The backend validates the request.
3. The backend asks the primary maps provider for routes.
4. If the primary provider fails, the backend retries through the fallback provider.
5. The backend resolves carrier rankings from the canonical business rules.
6. The backend returns a unified `SearchResponse`.
7. The frontend renders the routes, carrier list, and any user-facing error state.

## Package layout target
```text
genlogs_platform/
  specs/
  backend/
    app/
      api/
      services/
      providers/
      models/
      config/
  frontend/
    src/
      features/search/
      components/
      services/
  tests/
    backend/
    frontend/
    functional/
```

## Backend toolchain
| Concern | Tool |
|---|---|
| Language | Python 3.12+ |
| Framework | FastAPI |
| ASGI server | Uvicorn |
| Package manager | **uv** (Astral) — replaces pip for installs, virtual-env management, and lock-file generation |
| Dependency manifest | `pyproject.toml` with `uv.lock` |
| Linter | pylint (10.00/10 quality gate) |
| Architecture tests | archon-architecture + pytest |

## Backend responsibilities
1. Own all provider credentials and outbound provider calls.
2. Normalize city names and request payloads before business-rule evaluation.
3. Decide when to use the fallback provider.
4. Map provider errors into shared application errors.
5. Keep carrier rules independent from route-provider details.

## Frontend responsibilities
1. Collect user input on a single page.
2. Display suggestion lists, validation feedback, and asynchronous loading states.
3. Submit only selected city entities, not raw strings, for the main search request.
4. Render route summaries and carrier results from the backend contract.
5. Remain unaware of which maps provider is active.

## Configuration
1. `GENLOGS_MAPS_PROVIDER=google|mock`
2. `GENLOGS_GOOGLE_API_KEY=<secret>`
3. `GENLOGS_REQUEST_TIMEOUT_SECONDS=<int>`
4. `GENLOGS_RATE_LIMIT=100/minute` — rate limit applied to public endpoints; default `100/minute`

## Resilience patterns

### Outbound calls — providers layer (ADR-017)
All outbound HTTP calls made by the `providers` layer must apply:

| Pattern | Configuration |
|---|---|
| **Exponential retry** | Max 3 attempts (1 call + 2 retries). Backoff: 1 s → 2 s. Retry only on `502`, `503`, `504`, and network timeout. |
| **Circuit breaker** | Opens after 5 consecutive failures. Cool-down: 30 s. Half-open probe after cool-down. |

Libraries: `tenacity` (retry) + `pybreaker` (circuit breaker).  
Responsibility boundary: retry and circuit-breaker logic lives **only** in `providers/`. It must not be duplicated in `services` or `api/routes`.

When the primary provider's circuit is open or all retries are exhausted, `services` triggers the fallback provider.

### Inbound calls — api/routes layer (ADR-018)
Public endpoints are protected by a rate limiter:

| Endpoint | Limit |
|---|---|
| `GET /api/cities` | 100 requests / minute / client IP |
| `GET /api/search` | 100 requests / minute / client IP |
| `GET /health` | *(exempt)* |

Library: `slowapi`. Responses that exceed the limit return `429 Too Many Requests` with a `Retry-After` header.  
The limit value is configurable via `GENLOGS_RATE_LIMIT` in `backend/app/config/settings.py`.

## Error strategy
1. Validation errors return a stable `400` error response.
2. Unknown or unsupported routes return a user-readable `404` or domain-specific empty result, depending on the final implementation choice.
3. Provider failures return a stable `502`-style application error if both primary and fallback fail.
4. Provider-specific details stay in logs, not in public API messages.

## Delivery constraints
1. The MVP must be runnable locally.
2. The frontend should be easy to deploy as a static client or lightweight web app.
3. The backend should be deployable as a small web service.
4. The architecture spec should support the broader design writeup requested by the technical test.
