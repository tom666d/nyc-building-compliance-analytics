# ADR 0008: Separate blocking contracts from source-quality audits

Status: accepted

Amendment: ADR 0012 supersedes the uniform 99-percent blocking threshold for the legacy
violation fact after dashboard profiling exposed additional all-zero placeholder BIN records.
The quality scorecard continues to use 99 percent as the desired threshold.

## Context

Real source data contains valid operational ambiguity and known defects. The bounded sample includes two legacy violations without a usable Building Identification Number and two malformed issue dates. Failing every pipeline run on those known source records would make tests noisy; silently excluding them would hide material coverage limitations.

At the same time, changes such as a new unmapped status, snapshot reconciliation failure, duplicate grain, or a sharp drop in building-key coverage can directly corrupt published metrics and should stop the pipeline.

## Decision

Use two controls:

1. blocking dbt tests for transformation contracts and measurable service-level thresholds;
2. queryable audit views for retained source exceptions and a `PASS`/`WARN`/`ERROR` scorecard.

Building-key coverage must remain at or above 99%. Source freshness warns after 36 hours and errors after 72 hours. Any unmapped status is a blocking failure because the correct metric treatment has not been governed.

## Consequences

- Tests remain actionable instead of repeatedly failing on accepted source defects.
- Known exceptions stay visible at record level.
- Dashboard users can distinguish complete results from partial building-identity coverage.
- Thresholds are explicit hypotheses and must be recalibrated after full-volume baselines are available.
