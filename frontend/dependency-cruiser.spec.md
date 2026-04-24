# Frontend architecture validation

## Tool
`dependency-cruiser` configured via `frontend/.dependency-cruiser.cjs`.

## Rules in effect

| Rule | Boundary protected | Spec reference |
|------|--------------------|----------------|
| no-services-importing-ui | `services` must not import `components` or `features` | AT-012 |
| no-components-importing-features | `components` must not import `features` | AT-013 |
| no-circular-dependencies | No circular imports allowed | AT-005 |

## Running locally

```bash
cd frontend && npm run arch:validate
```

## Failure conditions
- Any violation listed above causes a non-zero exit and blocks the pre-commit hook and CI job.
