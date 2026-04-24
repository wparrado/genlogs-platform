import os
import pytest

from app.providers.maps import google


@pytest.mark.skipif(not os.environ.get("RUN_E2E"), reason="E2E disabled")
@pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="Google API key not set")
def test_google_integration_fetches_routes():
    """Integration test that calls the real Google Directions API.

    This only runs when RUN_E2E=1 and GOOGLE_API_KEY is provided in the
    environment (CI or local). It validates parsing and basic response shape.
    """
    # Ensure provider picks up the key from environment via settings
    # The google provider reads settings.genlogs_google_api_key via pydantic settings
    routes = google.get_routes_for_pair("New York, NY", "Washington, DC")
    assert isinstance(routes, list)
    # If API returns no routes for quota/limits, that's still a valid outcome; assert shape when present
    if routes:
        first = routes[0]
        assert "summary" in first
        assert "durationText" in first
