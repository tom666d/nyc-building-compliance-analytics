# Data quality and observability

## Quality contracts

Phase 1 separates blocking warehouse contracts from visible source-data exceptions.

| Quality dimension | Blocking contract | Visible audit behavior |
|---|---|---|
| Completeness | raw ingestion metadata is non-null; building-key coverage stays at or above 99% | unresolved records remain queryable with a reason |
| Uniqueness | declared fact and dimension keys remain unique | exact source duplicates are handled in staging |
| Validity | identifiers and governed status groups remain in accepted domains | source date parse failures retain the original value |
| Referential integrity | every non-null fact building key exists in `dim_buildings` | records without a defensible building key stay in the event fact |
| Consistency | status flags agree with status groups; lifecycle dates are not reversed | ambiguous source lifecycle combinations are profiled rather than guessed |
| Reconciliation | current snapshot totals equal independently calculated facts | failing queries return expected and actual measures |
| Timeliness | source age warns after 36 hours and errors after 72 hours | the scorecard exposes last ingestion time and age |

## Audit models

All quality models are current-state views in `DEV_MARTS`.

| Model | Purpose |
|---|---|
| `audit_data_quality_summary` | one scorecard row per event domain |
| `audit_unresolved_building_records` | detail records without a resolved building foreign key |
| `audit_date_anomalies` | reversed lifecycle dates and explicit date-parse failures |
| `audit_status_mapping_exceptions` | source statuses not covered by governed mappings |

The scorecard assigns:

- `ERROR` when a domain is empty, source age exceeds 72 hours, building-key coverage is below 99%, or any status is unmapped;
- `WARN` when source age exceeds 36 hours or a retained building/date exception exists;
- `PASS` otherwise.

An audit `WARN` does not make the dbt command fail. It distinguishes a known, measurable source limitation from a broken transformation contract.

## Reusable and singular tests

`not_null_proportion_at_least` is a project-owned generic data test. It fails when a model is empty or a declared column falls below the requested non-null proportion. Each event fact applies it to `building_key` with a minimum of 0.99.

Project-specific singular tests verify:

1. the current daily snapshot reconciles to independently aggregated facts and the building dimension;
2. boolean status flags agree with governed status groups;
3. permit and complaint lifecycle dates are not reversed;
4. no source status reaches a fact without a governed mapping;
5. the quality summary contains exactly the three Phase 1 domains.

## Verified Snowflake evidence

The full build on 2026-09-20 completed with:

```text
13 models
114 data tests
3 sources
1 exposure

PASS = 127
WARN = 0
ERROR = 0
NO-OP = 1 exposure
TOTAL = 128
```

Source freshness also passed independently for all three sources.

Current scorecard:

| Domain | Records | Building matches | Coverage | Unmapped statuses | Date anomalies | Source age | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| complaints | 1,000 | 1,000 | 100.00% | 0 | 0 | 5 hours | `PASS` |
| permit records | 1,000 | 1,000 | 100.00% | 0 | 0 | 5 hours | `PASS` |
| violations | 1,000 | 998 | 99.80% | 0 | 2 | 5 hours | `WARN` |

The violation detail views contain two missing/invalid BIN records and two issue-date parse failures. Status-mapping exceptions contain zero rows. Reader-role access to the scorecard was also verified.

## Commands

```text
make dbt-build
make dbt-freshness
make dbt-docs
```

`dbt build` validates transformation contracts. `dbt source freshness` is separate because it compares warehouse ingestion timestamps with current warehouse time rather than validating model rows.

## Current limitations

- Thresholds were selected for a bounded learning sample and need production-volume baselines.
- Freshness measures ingestion recency, not whether the city changed every underlying record.
- Audit views show current state rather than historical quality trends.
- Notification delivery is deferred to orchestration and monitoring work.
- Source exceptions are analytical signals, not official Department of Buildings corrections.
