"""Maps providers namespace.

Providers live under app.providers.maps and expose a compatible API used by
services. Two implementations are provided for MVP: a mock deterministic
provider (used by tests) and a Google provider (calls Directions API when an
API key is configured).
"""

from . import mock, google, google_places

__all__ = ["mock", "google", "google_places"]
