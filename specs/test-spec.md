# Test specification

## Testing approach
The MVP will follow a red-green-refactor loop:
1. Write or update the spec.
2. Write tests from the spec.
3. Implement the minimum code to satisfy the tests.
4. Refactor while keeping the tests green.

## Test layers
1. **Architecture tests**: validate backend layer boundaries with Archon and frontend boundaries with dependency-cruiser.
2. **Quality-gate checks**: validate backend `pylint` compliance and commit-time validation rules.
3. **Contract tests**: validate API payload shapes and status codes against the shared contract.
4. **Backend unit tests**: validate carrier rules, city normalization, provider fallback behavior, and error mapping.
5. **Backend integration tests**: validate FastAPI endpoints with provider stubs.
6. **Frontend component tests**: validate form behavior, loading states, results rendering, and error messages.
7. **Functional tests**: validate the main user flow across frontend and backend.

## Architecture test scenarios
1. The backend scaffold preserves the expected top-level layers: `api/routes`, `services`, `providers`, `models`, and `config`.
2. `api/routes` does not become a dependency target for lower layers.
3. `services` does not import from `api/routes`.
4. `providers` does not import from `api/routes`.
5. `models` remains independent from `api/routes`, `services`, and `providers`.
6. `config` remains independent from feature and infrastructure layers unless the spec is intentionally updated.
7. The frontend scaffold preserves the expected high-level areas: `features/search`, `components`, and `services`.
8. Frontend services do not import from UI layers.
9. Shared UI components do not import feature internals unless the spec is intentionally updated.
10. Structural drift that breaks the agreed scaffold layout causes the architecture validation to fail.

## Quality-gate scenarios
1. Backend `pylint` returns a score of `10.00/10` for commit-eligible changes.
2. A backend `pylint` score below `10.00/10` fails the commit gate.
3. Pre-commit blocks commits when backend Archon tests fail.
4. Pre-commit blocks commits when frontend architecture validation fails.
5. Pre-commit blocks commits when backend `pylint` fails or scores below the required threshold.
6. Using `# pylint: disable` or any configuration-level suppression to pass the quality gate is not permitted; the code must be fixed to satisfy the rule.
7. Any suppression that is genuinely necessary must be documented with a justification comment and cannot be introduced without explicit review.
6. Code that achieves `10.00/10` only by suppressing rules with `# pylint: disable` or equivalent bypass mechanisms is treated as a quality-gate violation regardless of the reported score.

## Backend test scenarios
### Carrier rules
1. Returns the New York -> Washington carrier ranking in the expected order.
2. Returns the San Francisco -> Los Angeles carrier ranking in the expected order.
3. Returns the generic fallback ranking for any non-special city pair.
4. Treats canonical aliases consistently, such as `NYC` vs `New York` if aliases are introduced in implementation.

### Search validation
1. Rejects requests with a missing `from` city.
2. Rejects requests with a missing `to` city.
3. Rejects requests where `from` and `to` are the same canonical city.
4. Rejects malformed payloads with a stable error shape.

### Provider behavior
1. Returns up to three routes ordered by travel time.
2. Uses the fallback provider only if the primary provider fails.
3. Returns a clear application error when both providers fail.
4. Maps provider-specific failures into shared API errors.

### City suggestions
1. Rejects empty or too-short search queries.
2. Returns normalized city suggestions for valid queries.
3. Returns an empty list for valid queries with no matches.

## Frontend test scenarios
1. Renders a single-page form with `From`, `To`, and `Search`.
2. Shows validation if the user tries to search without two valid selections.
3. Shows a loading state while the search request is in progress.
4. Renders route cards and carrier results after a successful search.
5. Renders a user-readable error message when the backend returns an error.
6. Handles an empty suggestion response without crashing.

## Functional test scenarios
1. User searches from New York to Washington DC and sees the expected carrier list plus three routes.
2. User searches from San Francisco to Los Angeles and sees the expected carrier list plus three routes.
3. User searches another valid pair and sees the generic fallback carrier list.
4. User triggers a provider failure and receives the correct fallback or final error behavior.

## Edge cases that must be covered before implementation is considered done
1. Missing input fields.
2. Same city selected twice.
3. Whitespace-only input.
4. Empty suggestion list.
5. Primary provider timeout or invalid API key.
6. Fallback provider failure after primary failure.
7. Unknown city payloads or stale client selections.

## Done criteria
1. All required happy-path scenarios are covered by automated tests.
2. Edge cases are captured before implementation completes.
3. The backend architecture baseline is protected by Archon tests.
4. The frontend architecture baseline is protected by architecture validation rules.
5. The backend quality gate is protected by `pylint` and pre-commit validation.
6. The functional test suite validates the full MVP search flow.
