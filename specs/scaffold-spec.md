# Scaffold specification

## Scope
This specification defines the expected scaffold for **Phase 1 / Activity 4**: creating the initial React frontend and FastAPI backend structure for the GenLogs MVP.

The purpose of this scaffold is to establish a runnable local development baseline, a base CI baseline, the initial backend packaging baseline, and local quality gates that protect the agreed architecture before changes are committed. Feature logic remains driven by the other specifications and the tests defined later.

## Expected outcome
At the end of this activity, the repository must contain:
1. A runnable FastAPI backend skeleton.
2. A runnable React frontend skeleton.
3. A shared package layout aligned with the architecture specification.
4. Minimal local configuration files for development.
5. A base shell for the search page and a health endpoint for the backend.
6. A base CI workflow that validates the scaffold automatically.
7. A backend Docker image definition aligned with the expected Google Cloud deployment path.
8. A package-root `.gitignore` and local Git repository bootstrap aligned with future remote publication.
9. Python architecture tests with Archon that protect the initial backend structure from unintended drift.
10. Frontend architecture validation that protects the initial React structure from unintended drift.
11. Pre-commit hooks that block commits when architecture checks fail or the backend does not achieve a `pylint` score of `10.00/10`.

## Tooling decisions
### Frontend
1. Framework: React
2. Language: TypeScript
3. Build tool: Vite
4. Package manager: npm

### Frontend architecture validation
1. Primary tool: `dependency-cruiser`
2. Fast feedback: ESLint import-boundary restrictions are allowed as a complementary guard
3. Purpose: protect frontend module boundaries and the initial feature/component/service structure

### Backend
1. Framework: FastAPI
2. Language: Python 3.12+
3. ASGI server: Uvicorn
4. Dependency management: `pyproject.toml`

### Backend static quality
1. Linter: `pylint`
2. Required commit threshold: `10.00/10`
3. Purpose: keep the backend scaffold strict and intentionally clean from the beginning

### Backend architecture validation
1. Library: `archon-architecture`
2. Test runner: pytest
3. Purpose: validate backend module boundaries and directory structure from the initial scaffold onward

### CI
1. Platform: GitHub Actions
2. Scope: frontend and backend validation on push and pull request

### Containerization
1. Backend packaging: Docker
2. Target runtime: Google Cloud Run compatible image
3. Frontend packaging: not required in the scaffold; static hosting remains acceptable

### Version control
1. Version control system: Git
2. Repository state: initialized locally at the `genlogs_platform` package root during scaffold setup
3. Publication target: remote-ready for GitHub, GitLab, or Bitbucket once the host is chosen

### Commit-time validation
1. Hook system: `pre-commit`
2. Scope: backend architecture tests, frontend architecture validation, and backend `pylint`
3. Goal: stop invalid commits before they enter the repository history

## Target directory structure
```text
genlogs_platform/
  .gitignore
  specs/
  .pre-commit-config.yaml
  .github/
    workflows/
      ci.yml
  backend/
    Dockerfile
    .dockerignore
    pyproject.toml
    app/
      __init__.py
      main.py
      api/
        __init__.py
        routes/
          __init__.py
          health.py
          search.py
      config/
        __init__.py
        settings.py
      services/
        __init__.py
      providers/
        __init__.py
      models/
        __init__.py
  frontend/
    package.json
    .dependency-cruiser.cjs
    .eslintrc.cjs
    tsconfig.json
    vite.config.ts
    src/
      main.tsx
      App.tsx
      features/
        search/
      components/
      services/
  tests/
    backend/
      test_architecture.py
    frontend/
      dependency-cruiser.spec.md
    functional/
```

## Backend scaffold requirements
### App bootstrap
- **BS-001** The backend must expose a FastAPI application entrypoint in `backend/app/main.py`.
- **BS-002** The application must register a `GET /health` endpoint.
- **BS-003** The application must reserve a route module for the future search endpoints, even if the business logic is not implemented yet.

### Configuration
- **BS-004** Backend configuration must be centralized in `backend/app/config/settings.py`.
- **BS-005** The scaffold must define placeholders for:
  1. `GENLOGS_ENV`
  2. `GENLOGS_MAPS_PROVIDER`
  3. `GENLOGS_GOOGLE_API_KEY`
  4. `GENLOGS_REQUEST_TIMEOUT_SECONDS`
- **BS-006** The backend must be runnable locally without a real Google key as long as the fallback provider mode is used.

### Containerization
- **BS-009** The backend scaffold must include a `Dockerfile` for producing a runnable application image.
- **BS-010** The backend image must target a simple production-style command compatible with FastAPI and Uvicorn.
- **BS-011** The Docker setup must avoid baking secrets into the image.
- **BS-012** The Docker setup must be suitable for later deployment to Google Cloud Run without requiring a redesign of the app entrypoint.

### Architecture protection
- **BS-013** The backend scaffold must include Python architecture tests using Archon.
- **BS-014** The Archon tests must validate both backend structure and import boundaries defined by the scaffold architecture.
- **BS-015** The architecture tests must be written early enough that later refactors fail fast if they break the intended layering accidentally.
- **BS-016** The scaffold must treat the Archon tests as part of the backend validation baseline, not as optional documentation.

### Backend quality gate
- **BS-017** The backend scaffold must include `pylint`.
- **BS-018** The backend scaffold must define a backend lint command that can be run locally and from hooks.
- **BS-019** The scaffold must treat a `pylint` score below `10.00/10` as a commit-blocking failure.
- **BS-020** Achieving `10.00/10` must be done by fixing the code, not by disabling, suppressing, or excluding `pylint` rules via inline comments (`# pylint: disable`), configuration ignores, or any other bypass mechanism.
- **BS-020** Disabling or excluding `pylint` rules via inline comments (`# pylint: disable`) or configuration suppressions to pass the score threshold is not permitted. The code must be corrected to satisfy the rule.
- **BS-021** Any legitimate suppression, such as a third-party API signature that cannot be changed, requires an explicit justification comment and must be approved before merging.

### Initial behavior
- **BS-007** `GET /health` must return a simple success payload suitable for local checks and later smoke tests.
- **BS-008** Any placeholder search route included in the scaffold must fail explicitly with a not-implemented response or a temporary stub response that cannot be confused with final behavior.

## Frontend scaffold requirements
### App bootstrap
- **FS-001** The frontend must expose a single-page React application.
- **FS-002** The main application shell must live in `frontend/src/App.tsx`.
- **FS-003** The initial screen must reserve sections for:
  1. search form
  2. route results
  3. carrier results
  4. error/status feedback

### Configuration
- **FS-004** The frontend scaffold must support a configurable backend base URL.
- **FS-005** The frontend must not contain provider secrets or direct Google API key usage in the browser.

### Initial behavior
- **FS-006** The initial shell may render placeholders, but it must reflect the intended MVP page structure.
- **FS-007** The scaffold must include a thin API client module location under `frontend/src/services/`.

### Frontend architecture protection
- **FS-008** The frontend scaffold must include an architecture validation baseline using `dependency-cruiser`.
- **FS-009** The frontend architecture validation must protect the agreed separation between `features`, `components`, and `services`.
- **FS-010** The scaffold may complement `dependency-cruiser` with ESLint import-boundary rules for faster local feedback.

## CI scaffold requirements
### Workflow scope
- **CI-001** The scaffold must include a GitHub Actions workflow file under `.github/workflows/ci.yml`.
- **CI-002** The workflow must run on `push` and `pull_request`.
- **CI-003** The workflow must validate the backend scaffold.
- **CI-004** The workflow must validate the frontend scaffold.

### Backend job
- **CI-005** The backend CI job must install Python and backend dependencies.
- **CI-006** The backend CI job must run at least the baseline checks needed for the scaffold, including the Archon architecture tests and the backend `pylint` quality gate once they are present.

### Frontend job
- **CI-007** The frontend CI job must install Node and frontend dependencies using `npm`.
- **CI-008** The frontend CI job must run the baseline checks for the scaffold, including frontend architecture validation and build validation once the frontend is created.

### Contract and failure behavior
- **CI-009** CI must fail when either the frontend or backend scaffold is broken.
- **CI-010** The workflow may stay minimal, but it must be structured so later tests and build steps can be expanded without redesigning the pipeline.

## Pre-commit scaffold requirements
### Hook scope
- **PC-001** The scaffold must include a package-root `.pre-commit-config.yaml`.
- **PC-002** Pre-commit must execute the backend Archon architecture tests before allowing a commit.
- **PC-003** Pre-commit must execute the frontend architecture validation before allowing a commit.
- **PC-004** Pre-commit must execute backend `pylint` before allowing a commit.

### Quality gate behavior
- **PC-005** A backend `pylint` score below `10.00/10` must block the commit.
- **PC-006** Failing backend or frontend architecture validation must block the commit.
- **PC-007** The hook configuration must be simple enough to run consistently in local development and CI-aligned environments.
- **PC-008** The `pylint` gate must not be satisfied through rule suppression; the only acceptable path to a passing score is clean, conformant code.

## Version control scaffold requirements
### Repository bootstrap
- **VC-001** The scaffold must initialize the `genlogs_platform` package root as a local Git repository.
- **VC-002** The scaffold must include a package-root `.gitignore`.
- **VC-003** The `.gitignore` must exclude local secrets, build outputs, dependency directories, Python caches, Node artifacts, and OS/editor noise.
- **VC-004** The repository state created at the package root must be clean enough to publish to a remote host without first removing generated noise by hand.

### Publication readiness
- **VC-005** The scaffold must stay compatible with later publication to a remote Git host such as GitHub, GitLab, or Bitbucket.
- **VC-006** Remote publication details are environment-dependent and do not need to be hardcoded into the scaffold itself.

## Architecture test requirements
### Scope of protection
- **AT-001** The backend scaffold must protect the intended layered structure: `api/routes`, `services`, `providers`, `models`, and `config`.
- **AT-002** Archon tests must fail when prohibited dependencies are introduced between protected backend layers.
- **AT-003** Archon tests must fail when the expected scaffold structure is broken or materially reorganized without updating the spec and tests together.
- **AT-004** Frontend architecture validation must protect the intended `features`, `components`, and `services` separation.
- **AT-005** Frontend architecture validation must fail when prohibited cross-layer imports are introduced.
- **AT-006** Frontend architecture validation must fail when the agreed scaffold structure is materially reorganized without updating the spec and validation rules together.

### Initial policy baseline
- **AT-007** `api/routes` may depend on `services`, `models`, and `config`.
- **AT-008** `services` may depend on `providers`, `models`, and `config`, but not on `api/routes`.
- **AT-009** `providers` may depend on `models` and `config`, but not on `api/routes`.
- **AT-010** `models` must remain independent of `api/routes`, `services`, and `providers`.
- **AT-011** `config` must remain independent of `api/routes`, `services`, `providers`, and `models`, except for shared settings primitives if explicitly introduced later.
- **AT-012** `frontend/src/services` must not import from UI layers such as `components` or `features`.
- **AT-013** Shared UI `components` must not import feature internals directly unless the spec is intentionally updated.
- **AT-014** `frontend/src/features/search` may depend on shared `components` and `services`, but not the reverse.

### Test placement
- **AT-015** The initial Archon tests should live under `tests/backend/test_architecture.py` or an equivalent backend test module that is clearly part of the automated suite.
- **AT-016** The frontend architecture validation rules should live near the frontend scaffold, such as `frontend/.dependency-cruiser.cjs`, with documentation or a small test note under `tests/frontend/`.
- **AT-017** The architecture tests must be runnable locally with the same validation commands used by CI and pre-commit.

## Local development contract
1. The backend must be runnable in development mode on a local port.
2. The frontend must be runnable in development mode on a local port.
3. The frontend must be able to point to the backend through configuration instead of hardcoded environment assumptions.
4. The backend image definition must be buildable locally without requiring production secrets.
5. The `genlogs_platform` package root must be locally versioned with Git from the scaffold stage onward.
6. The backend architecture tests must be runnable locally as part of the scaffold validation flow.
7. The frontend architecture validation must be runnable locally as part of the scaffold validation flow.
8. The backend `pylint` command must be runnable locally and produce a strict pass/fail result for the commit gate.
9. The scaffold must allow the project to grow into the contracts already defined in `product-spec.md`, `architecture-spec.md`, and `search-api.openapi.yaml`.

## Non-goals for this activity
1. Implementing the actual carrier rules.
2. Implementing real city suggestions.
3. Implementing real route lookup.
4. Completing frontend search interactions.
5. Completing full deployment automation for Google Cloud.
6. Defining every future architectural policy up front beyond the initial protected layers.
7. Enforcing frontend architecture constraints beyond the initial high-value boundaries.
8. Completing test coverage beyond what is needed to verify the scaffold exists, builds, and runs.

## Deliverables
1. Backend skeleton files and dependency manifest.
2. Frontend skeleton files and dependency manifest.
3. Initial environment examples or configuration placeholders.
4. A base GitHub Actions workflow for scaffold validation.
5. A backend Dockerfile and `.dockerignore`.
6. A package-root `.gitignore`.
7. A baseline Archon architecture test for the backend scaffold.
8. A baseline frontend architecture validation configuration.
9. A package-root `.pre-commit-config.yaml` with architecture and backend lint hooks.
10. Minimal run instructions in package-level documentation if needed during implementation.

## Done criteria
1. `backend` and `frontend` directories exist with the agreed structure.
2. The backend starts locally and answers `GET /health`.
3. The frontend starts locally and renders the MVP shell.
4. Configuration placeholders exist for provider selection and backend connectivity.
5. A base CI workflow exists and is capable of validating the scaffold.
6. The backend Docker image definition exists and is aligned with the intended Cloud Run deployment path.
7. A package-root `.gitignore` exists and covers the expected local/generated artifacts.
8. The `genlogs_platform` package root has been initialized as a local Git repository.
9. Archon-based backend architecture tests exist and fail when the scaffold layering is violated.
10. Frontend architecture validation exists and fails when the scaffold frontend boundaries are violated.
11. Pre-commit hooks exist for backend architecture validation, frontend architecture validation, and backend `pylint`.
12. A backend `pylint` score lower than `10.00/10` blocks the commit path.
13. No scaffold placeholder pretends to implement final business behavior.

## Implementation notes
1. Prefer the smallest viable scaffold that supports the later TDD phases.
2. Keep search logic, provider integrations, and carrier rules out of the scaffold unless needed to make the app boot.
3. Keep the CI scope intentionally small at first: install, basic validation, and later easy extension.
4. Containerization in this spec is for backend packaging readiness, not for fully solving deployment.
5. Use `.gitignore` to protect the repository from leaked secrets and generated noise from the start.
6. Keep the first Archon policy set intentionally small and high-value so it protects the scaffold without making early development brittle.
7. Keep the frontend architecture rules equally small and high-value so they protect structure without overfitting the early UI.
8. Use the scaffold only as structural groundwork; business behavior must continue to come from the specs and tests.
