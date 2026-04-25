import os
import sys
import pytest

# When tests run from repository root, ensure backend package directory is importable
# Compute project root (two levels up from tests/backend -> genlogs_platform)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BACKEND = os.path.join(ROOT, 'backend')
BACKEND_SRC = os.path.join(BACKEND, 'src')
# Insert backend src path so imports like `from app.main import app` work without setting PYTHONPATH
if BACKEND_SRC not in sys.path:
    sys.path.insert(0, BACKEND_SRC)
# Also insert backend path so modules in backend/ (e.g., scripts) can be imported directly
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

# Load project .env (if present) so tests can run without setting PYTHONPATH or DB env manually
ENV_PATH = os.path.join(ROOT, '.env')
if os.path.exists(ENV_PATH):
    try:
        with open(ENV_PATH, 'r', encoding='utf-8') as _envf:
            for _line in _envf:
                _line = _line.strip()
                if not _line or _line.startswith('#') or '=' not in _line:
                    continue
                _k, _v = _line.split('=', 1)
                _k = _k.strip()
                _v = _v.strip().strip('"').strip("'")
                # Set both original and upper-case variants so pydantic Settings picks them up
                os.environ.setdefault(_k, _v)
                os.environ.setdefault(_k.upper(), _v)
    except Exception:
        # Don't fail collection if .env cannot be read; continue with existing environment
        pass

# By default, skip long-running external E2E tests unless RUN_E2E=1 is set in the environment.
# Normalize RUN_E2E and treat only the literal string '1' as enabling E2E behavior.
RUN_E2E = os.environ.get("RUN_E2E", "").strip()

# Make tests deterministic by preferring the local mock provider for mock:* ids
# during normal unit/functional test runs. Integration/E2E tests (RUN_E2E=="1")
# will not enable this behavior.
import app.config.settings as cfg
import pytest

@pytest.fixture(scope="session", autouse=True)
def _prefer_mock_for_tests():
    # If RUN_E2E is not explicitly '1', enable mock provider preference for tests
    if RUN_E2E != "1":
        try:
            cfg.settings.genlogs_prefer_mock_for_mock_ids = True
        except Exception:
            # best-effort; tests will proceed with defaults if this fails
            pass

def pytest_collection_modifyitems(config, items):
    # Only skip E2E and integration tests when RUN_E2E is not '1'
    if RUN_E2E == "1":
        return
    skip_e2e = pytest.mark.skip(reason="E2E tests disabled by default; set RUN_E2E=1 to enable")
    for item in list(items):
        fpath = str(item.fspath)
        if "functional_e2e" in fpath or "/integration/" in fpath or "\\integration\\" in fpath:
            item.add_marker(skip_e2e)
