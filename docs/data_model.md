# Dimensional model

## Declared grains

| Model | Declared grain | Key |
|---|---|---|
| `dim_buildings` | one validated NYC Building Identification Number | BIN |
| `fct_permit_records` | one distinct DOB NOW approved-permit source payload | canonical source-row hash |
| `fct_complaints` | one latest-state DOB complaint | complaint number |
| `fct_violations` | one latest-state legacy BIS DOB violation record | ISN DOB BIS violation |
| `fct_building_compliance_daily` | one building per snapshot date | building key + snapshot date |
| `mart_building_compliance_current` | one building in the latest available snapshot | building key |
| `mart_borough_compliance_current` | one borough in the latest available snapshot | borough |
| `mart_compliance_overview` | one row for the latest available snapshot | snapshot date |

The permit model is deliberately named `fct_permit_records`. Live profiling did not produce a defensible real-world permit key, so the model does not claim that every source payload is one unique permit. Exact duplicate payloads are removed in staging; otherwise distinct source records remain available. ADR 0004 and ADR 0006 preserve this decision.

The daily snapshot is downstream of separately aggregated event facts. This prevents a many-to-many join among permits, complaints, and violations from multiplying measures.

## Dimension behavior

`dim_buildings` is a Type 1 conformed dimension. It contains one row per valid seven-digit BIN and stores current descriptive attributes rather than attribute history.

The selected observation is deterministic:

1. prefer a row with a valid ten-digit BBL;
2. prefer a row with borough;
3. prefer a complete house number and street name;
4. use source priority and ingestion time as tie-breakers.

The dimension also records the selected source, latest observation time across sources, and number of Phase 1 sources in which the BIN appeared.

## Status mappings

| Domain | Source value or category rule | Analytical group | Open/active behavior |
|---|---|---|---|
| complaint | `ACTIVE` | `ACTIVE` | counted as open |
| complaint | `CLOSED` | `RESOLVED` | not open |
| permit record | `PERMIT ISSUED` | `ISSUED` | active only if not expired on snapshot date |
| permit record | `SIGNED-OFF` | `SIGNED_OFF` | not active |
| violation | category contains `ACTIVE` | `ACTIVE` | counted as open |
| violation | category contains `RESOLVED` | `RESOLVED` | not open |
| violation | category contains `DISMISSED` | `DISMISSED` | not open |
| any domain | no governed rule matches | `UNKNOWN` | retained and not silently counted as open |

Violation status is not inferred from a null disposition date. Full-source profiling showed that the official category contains the meaningful lifecycle label and includes active variants for work without a permit, unserved Environmental Control Board cases, and hazardous conditions.

## Relationships

```text
dim_buildings (1) ----< fct_permit_records
              (1) ----< fct_complaints
              (1) ----< fct_violations
              (1) ----< fct_building_compliance_daily
fct_building_compliance_daily ----> mart_building_compliance_current
mart_building_compliance_current --> mart_borough_compliance_current
mart_building_compliance_current --> mart_compliance_overview
```

## Building identity strategy

1. A valid seven-digit BIN is the canonical business identifier.
2. BBL and normalized address remain descriptive candidates, never automatic equivalence rules in Phase 1.
3. Facts without a valid BIN receive a null building key and remain queryable in the event fact.
4. The building snapshot includes only resolved building keys and publishes source-coverage flags.

A usable BIN must start with borough code one through five, followed by six digits. Values such as
`0000000` are source placeholders, not building identities, and are retained only in event-level
facts with a null building key. This stricter rule was added after dashboard profiling exposed a
false building assembled from eleven unrelated legacy violation records.

## Consumption behavior

The three consumption marts select only the latest available daily snapshot. The building mart
adds a transparent workload attention score and tier; the borough and overview marts aggregate
that same governed result. The score is not a safety or legal risk classification. It ranks manual
review workload using open-item counts, recent complaints, and oldest-item age. Full definitions
and limits are documented in `docs/bi_consumption.md` and ADR 0012.

## Incremental snapshot behavior

`fct_building_compliance_daily` uses a Snowflake `MERGE` through dbt's incremental materialization.

- A same-day rerun updates the existing building/date rows.
- A run on a later warehouse date inserts a new daily partition.
- Historical rows are not recreated when late-arriving source data changes; this is an intentional Phase 1 limitation.
- `active_permit_record_count` is explicitly a source-record count, not a unique permit count.

## Verified bounded-sample results

The real Snowflake build on 2026-09-20 produced:

| Model | Rows |
|---|---:|
| `dim_buildings` | 2,383 |
| `fct_permit_records` | 1,000 |
| `fct_complaints` | 1,000 |
| `fct_violations` | 1,000 |
| `fct_building_compliance_daily` | 2,383 |

All three event facts matched their staging row counts. Building-key coverage was 1,000 of 1,000 permit records, 1,000 of 1,000 complaints, and 998 of 1,000 violations. The two violations without a valid BIN remain in `fct_violations` but are excluded from building rollups.

The daily snapshot contained 12 open complaints, 26 open violations, and one active permit source record. The event fact contained 28 active violations; two could not be assigned to a building because their BIN was missing. This visible difference is expected and documented, not a loss during transformation.

Those values describe the pre-Step-12 warehouse build. The dashboard review subsequently found
the `0000000` placeholder and reconciled the checked-in consumption snapshot to 2,382 usable
buildings and 15 open violations. The corrected Snowflake rebuild is pending the monthly resource
monitor reset, so the post-fix warehouse state is not presented as verified.
