# Architecture specification

## Architectural intent
The MVP should stay simple, implementation-friendly, and easy to demo. A lightweight layered architecture is enough for the requested scope.

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
1. The frontend submits the selected `from` and `to` cities to `POST /api/search`.
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
