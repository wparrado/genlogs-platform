"""Backend architecture tests using archon-architecture.

These tests protect the intended layered structure of the GenLogs backend.
They must fail when prohibited import dependencies are introduced between
the protected layers defined in the scaffold spec (AT-007 to AT-014).
"""
import os
import pytest


BASE = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app")


def _module(path: str) -> str:
    # Support legacy location app/models or new provider-backed location
    # app/providers/db/models. If the legacy path exists prefer it, otherwise
    # map models/... => providers/db/models/...
    candidate = os.path.normpath(os.path.join(BASE, path))
    if path.startswith("models") and not os.path.exists(candidate):
        suffix = path[len("models"):].lstrip(os.sep)
        candidate = os.path.normpath(os.path.join(BASE, "providers", "db", "models", suffix))
    return candidate


# ---------------------------------------------------------------------------
# Directory structure assertions
# ---------------------------------------------------------------------------

EXPECTED_DIRS = [
    "api",
    "api/routes",
    "config",
    "services",
    "providers",
    "models",
]


@pytest.mark.parametrize("subdir", EXPECTED_DIRS)
def test_expected_directory_exists(subdir: str) -> None:
    """Assert that the expected scaffold directories are present."""
    assert os.path.isdir(_module(subdir)), f"Expected directory missing: app/{subdir}"


EXPECTED_FILES = [
    "main.py",
    "api/__init__.py",
    "api/routes/__init__.py",
    "api/routes/health.py",
    "api/routes/search.py",
    "config/__init__.py",
    "config/settings.py",
    "services/__init__.py",
    "providers/__init__.py",
    "models/__init__.py",
]


@pytest.mark.parametrize("filepath", EXPECTED_FILES)
def test_expected_file_exists(filepath: str) -> None:
    """Assert that key scaffold files are present."""
    assert os.path.isfile(_module(filepath)), f"Expected file missing: app/{filepath}"


# ---------------------------------------------------------------------------
# Import boundary assertions (static source analysis)
# ---------------------------------------------------------------------------

def _read_source(path: str) -> str:
    full = _module(path)
    with open(full, encoding="utf-8") as f:
        return f.read()


def test_services_does_not_import_api_routes() -> None:
    """services must not depend on api/routes (AT-008)."""
    source = _read_source("services/__init__.py")
    assert "from app.api" not in source
    assert "import app.api" not in source


def test_providers_does_not_import_api_routes() -> None:
    """providers must not depend on api/routes (AT-009)."""
    source = _read_source("providers/__init__.py")
    assert "from app.api" not in source
    assert "import app.api" not in source


def test_models_does_not_import_api_routes() -> None:
    """models must remain independent of api/routes (AT-010)."""
    source = _read_source("models/__init__.py")
    assert "from app.api" not in source
    assert "import app.api" not in source


def test_models_does_not_import_services() -> None:
    """models must remain independent of services (AT-010)."""
    source = _read_source("models/__init__.py")
    assert "from app.services" not in source
    assert "import app.services" not in source


def test_models_does_not_import_providers() -> None:
    """models must remain independent of providers (AT-010)."""
    source = _read_source("models/__init__.py")
    assert "from app.providers" not in source
    assert "import app.providers" not in source


def test_config_does_not_import_api_routes() -> None:
    """config must remain independent of api/routes (AT-011)."""
    source = _read_source("config/settings.py")
    assert "from app.api" not in source
    assert "import app.api" not in source


def test_config_does_not_import_services() -> None:
    """config must remain independent of services (AT-011)."""
    source = _read_source("config/settings.py")
    assert "from app.services" not in source
    assert "import app.services" not in source


def test_config_does_not_import_providers() -> None:
    """config must remain independent of providers (AT-011)."""
    source = _read_source("config/settings.py")
    assert "from app.providers" not in source
    assert "import app.providers" not in source


def test_config_does_not_import_models() -> None:
    """config must remain independent of models (AT-011)."""
    source = _read_source("config/settings.py")
    assert "from app.models" not in source
    assert "import app.models" not in source
