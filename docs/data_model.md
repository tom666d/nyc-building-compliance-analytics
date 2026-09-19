# Dimensional model

## Fact grains

| Model | Declared grain | Natural key |
|---|---|---|
| `fct_permits` | provisional; permit issuance/work-type relationship requires refinement | no validated natural key yet |
| `fct_complaints` | one DOB complaint | complaint number |
| `fct_violations` | one legacy BIS DOB violation record | ISN DOB BIS violation |
| `fct_building_compliance_daily` | one building per snapshot date | building key + snapshot date |

The snapshot is intentionally downstream of event facts. This prevents a many-to-many join between permits, complaints, and violations, which would multiply measures.

The original permit-grain hypothesis failed live-source profiling. ADR 0004 records why the current permit fact scaffold must not be treated as production-ready. Exact source duplicates and legitimate multiple work types require separate handling.

## Dimensions

- `dim_buildings`: Type 1 conformed attributes (BIN, BBL, borough, address, geography) chosen from the most recently observed source values. Conflicts are surfaced as tests/audits.
- `dim_date`: calendar attributes for event and snapshot dates (Phase 2).
- status/type dimensions remain small governed seeds or semantic-layer labels until their business ownership is clearer.

## Relationships

```text
dim_buildings (1) ----< fct_permits
              (1) ----< fct_complaints
              (1) ----< fct_violations
              (1) ----< fct_building_compliance_daily >---- (1) dim_date [Phase 2]
```

## Building identity strategy

1. A valid seven-digit BIN is the canonical business identifier.
2. BBL and normalized address are descriptive/fallback candidates, never automatic equivalence in Phase 1.
3. Facts without valid BIN receive a null building key and stay queryable in the event fact.
4. The BI snapshot only includes resolved building keys and publishes source coverage flags.

## Snapshot behavior

The Phase 1 snapshot is current-state-as-of-run. Historical daily persistence will be implemented as a dbt snapshot or incremental append after source late-arrival behavior is measured. Naming the model `daily` declares the intended product grain; the initial SQL produces today's partition.
