# Product specification

## Product summary
GenLogs needs an MVP portal that lets a user choose a source city and a destination city, view the fastest three routes between them, and see the carriers moving the most trucks across that corridor.

The MVP is a simulation of the portal requested in the technical test, but it should be structured so it can evolve into the full GenLogs platform later.

## Goals
1. Deliver a single-page search experience.
2. Use backend-controlled integrations so API keys stay server-side.
3. Return deterministic carrier rankings for the required city pairs.
4. Keep the contract stable whether Google services or a fallback provider is active.

## Non-goals
1. User authentication or authorization.
2. Persistent storage for the portal simulation.
3. Analytics, billing, or admin tooling.
4. Full production coverage of the broader image-processing platform.

## Primary user
An internal or interview reviewer who wants to validate the search experience from city selection through route and carrier results.

## User flow
1. The user opens a single-page web application.
2. The user types a source city and selects one valid suggestion.
3. The user types a destination city and selects one valid suggestion.
4. The user clicks `Search`.
5. The frontend sends the selected city payloads to the backend.
6. The backend resolves the route options and the carrier list.
7. The frontend renders the fastest three routes and the ranked carrier results.
8. If anything fails, the frontend shows a clear error state without exposing provider-specific internals.

## Functional requirements
### Search experience
- **FR-001** The UI must expose `From`, `To`, and `Search` controls on a single page.
- **FR-002** City selection must be backed by backend-provided suggestions so secrets remain server-side.
- **FR-003** The user must select two valid and distinct cities before the search is considered valid.
- **FR-004** The UI must render loading, success, empty, and error states explicitly.

### Routes
- **FR-005** The backend must return the fastest three routes ordered by travel time when the provider can supply them.
- **FR-006** Each route result must include enough information to render a readable summary: an identifier, summary label, duration text, distance text, and optional map embed URL or provider-safe path data.
- **FR-007** The primary maps provider should be queried first. A fallback provider may be used only if the primary provider fails.

### Carrier ranking
- **FR-008** Carrier results must be returned in descending rank order by `trucksPerDay`.
- **FR-009** The following canonical city pairs must return fixed carrier results:
  1. `New York, NY` -> `Washington, DC`
     1. Knight-Swift Transport Services - 10 trucks/day
     2. J.B. Hunt Transport Services Inc - 7 trucks/day
     3. YRC Worldwide - 5 trucks/day
  2. `San Francisco, CA` -> `Los Angeles, CA`
     1. XPO Logistics - 9 trucks/day
     2. Schneider - 6 trucks/day
     3. Landstar Systems - 2 trucks/day
- **FR-010** Any city pair outside the two named pairs must return the generic fallback carrier list unless a tighter business rule is later confirmed:
  1. UPS Inc. - 11 trucks/day
  2. FedEx Corp - 9 trucks/day

### API and reliability
- **FR-011** Backend responses must use a shared error shape with `code`, `message`, and optional `details`.
- **FR-012** The backend must expose a health endpoint for local checks and deployment smoke tests.

## Non-functional requirements
1. The frontend and backend must be independently runnable in local development.
2. The backend must hide all provider credentials from the browser.
3. The same API contract must hold whether the primary provider or fallback provider is active.
4. Validation failures must be deterministic and readable.
5. The implementation must be test-first and cover edge cases before feature completion.

## Acceptance criteria
1. A user can complete a full search on one page without page navigation.
2. Route results show up to three fastest routes for a valid city pair.
3. Carrier results match the required ranking rules for the two named pairs and the generic fallback.
4. Missing inputs, same-city searches, and provider failures return explicit, user-visible errors.
5. The same frontend behavior works against either the primary or fallback provider.

## Open assumptions
1. The Google-backed implementation is preferred for route and city lookup.
2. The portal simulation does not require database persistence.
3. Mixed city pairs such as `New York -> Los Angeles` are treated as generic fallback pairs unless the business rule is refined later.
