# Database specification

## Scope
This specification models **only the data required to support the MVP features**:
1. City autocomplete fallback when Google Maps is unavailable.
2. Carrier master data for the required carrier rankings.
3. Carrier route rules encoding the business logic from FR-009 and FR-010.

The MVP portal itself is largely stateless (no user sessions, no search history).
The database exists to make the carrier ranking rules and city fallback data queryable and maintainable
without hardcoding them in application code.

---

## Entities

### 1. `city_reference`
Stores normalized city entities used as the autocomplete fallback when the Google Maps provider
is unavailable (circuit open) or the mock provider is active.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK | Stable internal identifier |
| `place_id` | `VARCHAR(255)` | UNIQUE | Google Maps place ID, or a mock ID in test data |
| `name` | `VARCHAR(100)` | NOT NULL | City display name (e.g., `New York`) |
| `state` | `VARCHAR(100)` | NOT NULL | State or region (e.g., `NY`) |
| `country` | `VARCHAR(10)` | NOT NULL, DEFAULT `'US'` | ISO country code |
| `normalized_label` | `VARCHAR(200)` | NOT NULL | Searchable label: `new york, ny, us` (lowercased) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | Record creation time |

**Indexes:**
- `idx_city_reference_normalized_label` on `normalized_label` — supports prefix search for autocomplete.
- `idx_city_reference_place_id` on `place_id` — supports deduplication on upsert.

**Seed data required (minimum):**
The following cities must be present to support the two canonical carrier rule pairs (FR-009):

| `name` | `state` | `normalized_label` |
|---|---|---|
| New York | NY | `new york, ny, us` |
| Washington | DC | `washington, dc, us` |
| San Francisco | CA | `san francisco, ca, us` |
| Los Angeles | CA | `los angeles, ca, us` |

---

### 2. `carriers`
Stores the carrier entities referenced in carrier ranking results.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK | Stable internal identifier |
| `name` | `VARCHAR(200)` | NOT NULL, UNIQUE | Full carrier display name |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `TRUE` | Soft-disable a carrier without deleting rules |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | Record creation time |

**Seed data required:**

| `name` |
|---|
| Knight-Swift Transport Services |
| J.B. Hunt Transport Services Inc |
| YRC Worldwide |
| XPO Logistics |
| Schneider |
| Landstar Systems |
| UPS Inc. |
| FedEx Corp |

---

### 3. `carrier_route_rules`
Encodes the carrier ranking business rules from FR-009 and FR-010.

A rule with `origin_city_id IS NULL AND destination_city_id IS NULL` is the **generic default rule**
applied to any city pair that has no specific rule defined.

A rule with both city IDs set is a **specific route override** for that exact city pair.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PK | Stable internal identifier |
| `origin_city_id` | `UUID` | FK → `city_reference.id`, NULLABLE | Origin city; NULL means generic default |
| `destination_city_id` | `UUID` | FK → `city_reference.id`, NULLABLE | Destination city; NULL means generic default |
| `carrier_id` | `UUID` | FK → `carriers.id`, NOT NULL | The carrier this rule applies to |
| `daily_trucks` | `SMALLINT` | NOT NULL, CHECK ≥ 0 | Trucks per day — results are ordered by this value descending (FR-008) |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `NOW()` | Record creation time |

**Unique constraint:** `(origin_city_id, destination_city_id, carrier_id)` — one rule per carrier per route.

**Indexes:**
- `idx_carrier_route_rules_cities` on `(origin_city_id, destination_city_id)` — used in every route search query.

**Seed data required (from FR-009 and FR-010):**

*New York, NY → Washington, DC:*

| `origin` | `destination` | `carrier` | `daily_trucks` |
|---|---|---|---|
| New York, NY | Washington, DC | Knight-Swift Transport Services | 10 |
| New York, NY | Washington, DC | J.B. Hunt Transport Services Inc | 7 |
| New York, NY | Washington, DC | YRC Worldwide | 5 |

*San Francisco, CA → Los Angeles, CA:*

| `origin` | `destination` | `carrier` | `daily_trucks` |
|---|---|---|---|
| San Francisco, CA | Los Angeles, CA | XPO Logistics | 9 |
| San Francisco, CA | Los Angeles, CA | Schneider | 6 |
| San Francisco, CA | Los Angeles, CA | Landstar Systems | 2 |

*Generic default (any other pair):*

| `origin` | `destination` | `carrier` | `daily_trucks` |
|---|---|---|---|
| NULL | NULL | UPS Inc. | 11 |
| NULL | NULL | FedEx Corp | 9 |

---

## Query patterns

### Carrier lookup for a route
```sql
-- 1. Try specific rule for the given city pair
SELECT c.name, r.daily_trucks
FROM carrier_route_rules r
JOIN carriers c ON c.id = r.carrier_id
WHERE r.origin_city_id = :origin_id
  AND r.destination_city_id = :destination_id
  AND c.is_active = TRUE
ORDER BY r.daily_trucks DESC;

-- 2. If no rows returned, fall back to generic default
SELECT c.name, r.daily_trucks
FROM carrier_route_rules r
JOIN carriers c ON c.id = r.carrier_id
WHERE r.origin_city_id IS NULL
  AND r.destination_city_id IS NULL
  AND c.is_active = TRUE
ORDER BY r.daily_trucks DESC;
```

### City autocomplete fallback
```sql
SELECT id, name, state, country, normalized_label
FROM city_reference
WHERE normalized_label LIKE :prefix || '%'
ORDER BY normalized_label
LIMIT 10;
```

---

## Relationship summary
```
city_reference ←── carrier_route_rules ───→ city_reference
                         │
                         └──────────────────→ carriers
```

- One `city_reference` row can appear as origin or destination in many `carrier_route_rules`.
- One `carriers` row can appear in many `carrier_route_rules` (across multiple routes).
- The generic default rule has no city reference FK (both are NULL).

---

## Non-goals for this spec
1. Search history or user sessions.
2. Camera captures, image processing, plate detection.
3. USDOT or FMCSA regulatory data.
4. Corridor analytics or truck observation data.
5. Any table not directly required by the city autocomplete or carrier ranking features.
