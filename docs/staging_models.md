# dbt staging models

## Purpose

The staging layer is the first typed representation of the append-only NYC Open Data payloads. It keeps source meaning visible while making field names, data types, borough values, date parsing, and exact-payload deduplication consistent for downstream models.

All three staging models are views in `NYC_DOB_ANALYTICS.DEV_STAGING`. Views avoid storing a second physical copy of the bounded learning sample while the transformation rules are still being refined.

## Model grains

| Model | Grain | Key behavior |
|---|---|---|
| `stg_dob_now_permits` | one distinct source payload | `source_row_hash` is a technical content key because no source natural key passed profiling |
| `stg_dob_complaints` | latest source state per complaint number | exact payload duplicates are removed before version ranking |
| `stg_dob_violations` | latest source state per legacy violation ID | exact payload duplicates are removed before version ranking |

The permit model deliberately does not collapse rows using job filing number, work permit, and sequence number. Live profiling showed that combination can represent several tracking numbers and work types.

## Standardization rules

- Valid BIN values contain exactly seven digits; invalid values become null without removing the source row.
- Borough codes and names resolve to one of the five uppercase canonical borough names.
- Permit ISO timestamps are converted to dates through `TRY_TO_TIMESTAMP_NTZ`.
- Complaint dates use the explicit `MM/DD/YYYY` format.
- Legacy violation dates use the explicit `YYYYMMDD` format and must represent years 1900 through 2099.
- Source identifiers, row hashes, load identifiers, and ingestion timestamps remain available for lineage.

## Visible data-quality behavior

The first 1,000-row violation sample contained source values `02230913` and `0306`. Automatic date conversion would interpret the first value as the year 223. The staging model instead:

1. preserves the original value in `source_issue_date`;
2. returns null in `issue_date`;
3. sets `issue_date_parse_failed` to true.

This makes the exception measurable without guessing a corrected date or dropping the record.

## Verified build

On 2026-09-20, dbt created all three staging views against the real Snowflake account. The build executed 13 data tests covering key completeness, uniqueness, normalized borough values, BIN format, and non-null parse flags. The final result was 16 passes: three view models plus 13 tests.

The bounded warehouse sample contained:

| Model | Rows |
|---|---:|
| `stg_dob_now_permits` | 1,000 |
| `stg_dob_complaints` | 1,000 |
| `stg_dob_violations` | 1,000 |

## Current limitation

This milestone validates staging behavior on a bounded real-data sample, not all 6.6 million source rows. The permit key remains technical rather than a validated business key. Fact-model release decisions remain deferred to the dimensional-model milestone.
