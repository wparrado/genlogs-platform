# genlogs_platform specifications

This directory is the source of truth for the GenLogs MVP and follows a Specification-Driven Development approach.

## Spec set
1. `product-spec.md`: MVP scope, user flow, functional behavior, and acceptance criteria.
2. `architecture-spec.md`: module boundaries, information flow, configuration, and runtime decisions.
3. `scaffold-spec.md`: detailed specification for Phase 1 Activity 4, covering the initial React and FastAPI project scaffold.
4. `database-spec.md`: database design for the broader GenLogs platform deliverable.
5. `search-api.openapi.yaml`: machine-readable API contract for the MVP backend.
6. `test-spec.md`: TDD scenarios, contract tests, edge cases, and functional test coverage.

## Intended package layout
The package will evolve to contain:

```text
genlogs_platform/
  specs/
  backend/
  frontend/
  tests/
```

## Current assumptions
1. The MVP is a single-page React client plus a FastAPI backend.
2. Google services are the primary provider for city lookup and routes.
3. A fallback maps provider is available if the primary provider fails or cannot be configured.
4. For carrier results, the two named city pairs are special cases and every other pair uses the generic fallback list unless the business rule is refined later.
