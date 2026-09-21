# Data quality and observability

## Quality contracts

Phase 1 separates blocking warehouse contracts from visible source-data exceptions.

| Quality dimension | Blocking contract | Visible audit behavior |
|---|---|---|
| Completeness | raw ingestion metadata is non-null; permit and complaint coverage stays at or above 99%, while legacy violations use a documented 98% blocking floor | the scorecard retains a 99% desired threshold and unresolved records remain queryable with a reason |
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

`not_null_proportion_at_least` is a project-owned generic data test. It fails when a model is
empty or a declared column falls below the requested non-null proportion. Permit and complaint
facts require 0.99. The legacy violation fact uses a 0.98 blocking floor after dashboard profiling
found eleven records grouped under an unusable all-zero BIN. The audit scorecard still marks
coverage below 99% as `ERROR`; ADR 0012 records why the blocking and observability thresholds now
differ for this source.

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

Step 12 dashboard profiling subsequently found that `0000000` had passed the original seven-digit
syntax check and grouped eleven additional legacy violations under a false building. The revised
normalization requires borough code one through five and rejects borough-zero placeholders. That
change projects legacy violation building-key coverage to 98.70% and removes the pseudo-building
from consumption metrics. A post-correction Snowflake rebuild is pending the monthly resource
monitor reset, so the table above remains the last fully verified pre-correction scorecard.

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
- The post-zero-BIN normalization state is parsed and snapshot-reconciled locally but not yet rebuilt in Snowflake because the configured resource monitor has reached its monthly quota.
