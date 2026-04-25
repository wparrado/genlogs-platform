Google Routes provider (ComputeRoutes)

This provider uses the Google Routes API (ComputeRoutes endpoint) via HTTP POST.

Key behavior:
- computeAlternativeRoutes is set to true to request alternative routes.
- The provider requests the following fields via X-Goog-FieldMask:
  routes.duration,routes.distanceMeters,routes.description,routes.polyline.encodedPolyline
- Encoded polylines (routes.polyline.encodedPolyline) are decoded into pathPayload (list of [lat, lng]).
- Routes are returned sorted by duration (shortest first).
- Route IDs are derived strictly from routes.description when present. summary is NOT used for ID generation; if description is missing the provider falls back to a google_{idx} id (index-based).
- Origin/destination are sent as waypoint.placeId when possible; otherwise as address strings.

Notes:
- If you need more detailed truck routing (dimensions, axle count, restrictions) add truckInfo/vehicleInfo to the request body or use the official gRPC client.
- The provider performs simple retry/backoff and an in-process circuit breaker.

Field mapping (response -> normalized):
- routes.duration -> duration (int seconds) and durationText (original text)
- routes.distanceMeters -> distance (int)
- routes.description -> used to generate the route "id" (sanitized)
- routes.polyline.encodedPolyline -> decoded into pathPayload

