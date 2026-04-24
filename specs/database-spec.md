# Database specification

## Scope of this design
The technical test asks for a database design for the broader GenLogs platform, even though the MVP portal simulation itself does not need database storage. This spec therefore defines the long-term platform data model and explicitly keeps the MVP app stateless for now.

## Design goals
1. Store highway camera captures and detection outputs.
2. Link plate or truck-number evidence to carriers and trucks.
3. Preserve external regulatory enrichments from USDOT and Safer FMCSA.
4. Support corridor analytics such as carrier traffic between city pairs.

## Core entities
### 1. camera_locations
Stores the highway cameras operated by the platform.

Key fields:
- `id`
- `name`
- `highway_code`
- `latitude`
- `longitude`
- `city`
- `state`
- `is_active`

### 2. captured_images
Stores image capture metadata.

Key fields:
- `id`
- `camera_location_id`
- `captured_at`
- `image_uri`
- `processing_status`
- `checksum`

### 3. plate_candidates
Stores OCR outputs or truck-number candidates detected from images.

Key fields:
- `id`
- `captured_image_id`
- `candidate_text`
- `confidence_score`
- `bounding_box`

### 4. logo_detections
Stores logo matches found in the image.

Key fields:
- `id`
- `captured_image_id`
- `carrier_name_detected`
- `confidence_score`
- `bounding_box`

### 5. carriers
Stores normalized carrier identities.

Key fields:
- `id`
- `name`
- `usdot_number`
- `mc_number`
- `status`

### 6. trucks
Stores normalized truck identities when they can be inferred.

Key fields:
- `id`
- `carrier_id`
- `plate_number`
- `plate_state`
- `truck_number`
- `last_verified_at`

### 7. truck_observations
Stores the best-effort link between a detected truck and a camera event.

Key fields:
- `id`
- `captured_image_id`
- `truck_id`
- `carrier_id`
- `observation_confidence`
- `matched_from`

### 8. usdot_profiles
Stores normalized enrichment data from USDOT.

Key fields:
- `id`
- `carrier_id`
- `legal_name`
- `physical_address`
- `fleet_size`
- `snapshot_taken_at`

### 9. safer_fmcsa_snapshots
Stores periodic compliance snapshots from Safer FMCSA.

Key fields:
- `id`
- `carrier_id`
- `safety_rating`
- `insurance_status`
- `inspection_count`
- `snapshot_taken_at`

### 10. city_reference
Stores normalized city entities for reporting and aggregation.

Key fields:
- `id`
- `provider_place_id`
- `city`
- `state`
- `country`
- `normalized_label`

### 11. inferred_trips
Stores inferred movement between two observations.

Key fields:
- `id`
- `truck_id`
- `origin_observation_id`
- `destination_observation_id`
- `origin_city_id`
- `destination_city_id`
- `started_at`
- `ended_at`
- `inference_score`

### 12. corridor_daily_stats
Stores aggregate counts used by the portal-style analysis layer.

Key fields:
- `id`
- `origin_city_id`
- `destination_city_id`
- `carrier_id`
- `stat_date`
- `truck_count`

## Relationship summary
1. One camera location has many captured images.
2. One captured image can have many plate candidates and logo detections.
3. One carrier can have many trucks and many regulatory snapshots.
4. One truck can have many observations and inferred trips.
5. Corridor aggregates roll up inferred trips by city pair, carrier, and day.

## Indexing guidance
1. Index `captured_images(camera_location_id, captured_at)`.
2. Index `plate_candidates(candidate_text)`.
3. Index `carriers(usdot_number)` and `carriers(name)`.
4. Index `trucks(plate_number, plate_state)` and `trucks(truck_number)`.
5. Index `corridor_daily_stats(origin_city_id, destination_city_id, stat_date)`.

## MVP note
The portal simulation for the technical test should not depend on these tables. Carrier results can remain in code for the MVP while this design supports the separate database-design deliverable.
