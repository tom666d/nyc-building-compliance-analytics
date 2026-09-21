# ADR 0007: Persist the building snapshot incrementally

Status: accepted

## Context

A table rebuilt with `current_date` would only represent the latest run even if its name implied daily history. The Business Intelligence layer needs one stable building/date grain and should not duplicate a date when a pipeline is retried.

## Decision

Materialize `fct_building_compliance_daily` as a dbt incremental model using Snowflake `MERGE` and the compound unique key `snapshot_date + building_key`.

- A same-day rerun updates the current date's rows.
- A later run inserts another daily partition.
- Event facts are aggregated independently before joining to the building dimension.

## Consequences

- Pipeline retries are idempotent at the declared snapshot grain.
- Daily history begins on the first successful scheduled run.
- Late-arriving changes update only the current run's partition; accurate historical restatement is deferred until late-arrival behavior is measured.
- The snapshot uses `active_permit_record_count` because the permit business grain is not yet validated.
