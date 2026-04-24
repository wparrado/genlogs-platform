# Scaffold specification

## Scope
This specification defines the expected scaffold for **Phase 1 / Activity 4**: creating the initial React frontend and FastAPI backend structure for the GenLogs MVP.

The purpose of this scaffold is to establish a runnable local development baseline, a base CI baseline, and the initial backend packaging baseline, not to complete feature behavior. Feature logic remains driven by the other specifications and the tests defined later.

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

## Tooling decisions
### Frontend
1. Framework: React
2. Language: TypeScript
3. Build tool: Vite
4. Package manager: npm

### Backend
1. Framework: FastAPI
2. Language: Python 3.12+
3. ASGI server: Uvicorn
4. Dependency management: `pyproject.toml`

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

## Target directory structure
```text
genlogs_platform/
  .gitignore
  specs/
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
    frontend/
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

## CI scaffold requirements
### Workflow scope
- **CI-001** The scaffold must include a GitHub Actions workflow file under `.github/workflows/ci.yml`.
- **CI-002** The workflow must run on `push` and `pull_request`.
- **CI-003** The workflow must validate the backend scaffold.
- **CI-004** The workflow must validate the frontend scaffold.

### Backend job
- **CI-005** The backend CI job must install Python and backend dependencies.
- **CI-006** The backend CI job must run at least the baseline checks needed for the scaffold, such as tests or import-level validation once those are present.

### Frontend job
- **CI-007** The frontend CI job must install Node and frontend dependencies using `npm`.
- **CI-008** The frontend CI job must run the baseline checks for the scaffold, including build validation once the frontend is created.

### Contract and failure behavior
- **CI-009** CI must fail when either the frontend or backend scaffold is broken.
- **CI-010** The workflow may stay minimal, but it must be structured so later tests and build steps can be expanded without redesigning the pipeline.

## Version control scaffold requirements
### Repository bootstrap
- **VC-001** The scaffold must initialize the `genlogs_platform` package root as a local Git repository.
- **VC-002** The scaffold must include a package-root `.gitignore`.
- **VC-003** The `.gitignore` must exclude local secrets, build outputs, dependency directories, Python caches, Node artifacts, and OS/editor noise.
- **VC-004** The repository state created at the package root must be clean enough to publish to a remote host without first removing generated noise by hand.

### Publication readiness
- **VC-005** The scaffold must stay compatible with later publication to a remote Git host such as GitHub, GitLab, or Bitbucket.
- **VC-006** Remote publication details are environment-dependent and do not need to be hardcoded into the scaffold itself.

## Local development contract
1. The backend must be runnable in development mode on a local port.
2. The frontend must be runnable in development mode on a local port.
3. The frontend must be able to point to the backend through configuration instead of hardcoded environment assumptions.
4. The backend image definition must be buildable locally without requiring production secrets.
5. The `genlogs_platform` package root must be locally versioned with Git from the scaffold stage onward.
6. The scaffold must allow the project to grow into the contracts already defined in `product-spec.md`, `architecture-spec.md`, and `search-api.openapi.yaml`.

## Non-goals for this activity
1. Implementing the actual carrier rules.
2. Implementing real city suggestions.
3. Implementing real route lookup.
4. Completing frontend search interactions.
5. Completing full deployment automation for Google Cloud.
6. Completing test coverage beyond what is needed to verify the scaffold exists, builds, and runs.

## Deliverables
1. Backend skeleton files and dependency manifest.
2. Frontend skeleton files and dependency manifest.
3. Initial environment examples or configuration placeholders.
4. A base GitHub Actions workflow for scaffold validation.
5. A backend Dockerfile and `.dockerignore`.
6. A package-root `.gitignore`.
7. Minimal run instructions in package-level documentation if needed during implementation.

## Done criteria
1. `backend` and `frontend` directories exist with the agreed structure.
2. The backend starts locally and answers `GET /health`.
3. The frontend starts locally and renders the MVP shell.
4. Configuration placeholders exist for provider selection and backend connectivity.
5. A base CI workflow exists and is capable of validating the scaffold.
6. The backend Docker image definition exists and is aligned with the intended Cloud Run deployment path.
7. A package-root `.gitignore` exists and covers the expected local/generated artifacts.
8. The `genlogs_platform` package root has been initialized as a local Git repository.
9. No scaffold placeholder pretends to implement final business behavior.

## Implementation notes
1. Prefer the smallest viable scaffold that supports the later TDD phases.
2. Keep search logic, provider integrations, and carrier rules out of the scaffold unless needed to make the app boot.
3. Keep the CI scope intentionally small at first: install, basic validation, and later easy extension.
4. Containerization in this spec is for backend packaging readiness, not for fully solving deployment.
5. Use `.gitignore` to protect the repository from leaked secrets and generated noise from the start.
6. Use the scaffold only as structural groundwork; business behavior must continue to come from the specs and tests.
