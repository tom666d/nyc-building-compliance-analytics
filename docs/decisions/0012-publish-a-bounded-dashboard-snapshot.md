# ADR 0012: Publish a bounded dashboard snapshot with transparent prioritization

- Status: Accepted
- Date: 2026-09-21
- Supersedes: the uniform 99-percent blocking threshold in ADR 0008 for legacy violations only

## Context

The portfolio needs a shareable consumption layer, but a browser cannot safely receive Snowflake
credentials. A live connection would also resume the warehouse for every viewing session. The
current raw ingestion is intentionally bounded to 1,000 rows per source and should not be
presented as a citywide population.

The daily snapshot contains open complaint and violation workload but no validated regulatory
severity field. A dashboard still needs a consistent review order without implying structural
risk. During consumption profiling, an all-zero `0000000` source value also passed the original
seven-digit Building Identification Number rule and grouped eleven violations under a false
building.

## Decision

1. Publish three dbt consumption marts at building, borough, and portfolio grains.
2. Define a zero-to-100 attention score from open complaints, open violations, recent complaints,
   and oldest-open-item age, with fixed, documented tier thresholds.
3. Name and describe the score as workload prioritization, never structural or legal risk.
4. Export a versioned JSON snapshot with the least-privilege reader role and import it at website
   build time.
5. Validate dashboard rollups, identifiers, categories, and arithmetic before each build.
6. Require a usable Building Identification Number to start with borough code one through five
   and reject borough-zero placeholder patterns.
7. Keep a 99-percent desired building-key coverage threshold in the quality scorecard. Allow the
   legacy violation fact to build at a 98-percent blocking floor so retained known source defects
   remain visible as `ERROR` rather than preventing every development build.
8. Disclose the bounded source scope and snapshot date in the primary interface.

## Consequences

### Benefits

- The shareable dashboard contains no Snowflake credentials and has no per-page warehouse cost.
- Metric definitions remain in dbt and are reusable by another business intelligence tool.
- Review ordering is explainable, deterministic, and testable.
- A source placeholder cannot become a false building-level decision record.
- Source-quality degradation stays visible rather than being filtered from the fact tables.
- The dashboard can be reproduced from a small versioned contract.

### Costs and limitations

- The site is only as current as its last explicit export.
- A static bounded queue is not a full operational application.
- The attention score weights are policy hypotheses, not statistically learned coefficients.
- The legacy violation blocking floor differs from the desired scorecard threshold and therefore
  requires explicit documentation.
- Rebuilding the corrected Snowflake models must wait for resource-monitor capacity; the checked-in
  snapshot is reconciled from the last verified aggregate until then.

## Alternatives considered

### Connect the browser directly to Snowflake

Rejected because it would expose an inappropriate credential boundary, create warehouse cost per
session, and make a public portfolio dependent on a live trial account.

### Put all metric and scoring logic in the React application

Rejected because another consumer could then calculate different values. Business logic belongs
in governed transformation models, while the application owns interaction and presentation.

### Call the composite value a risk score

Rejected because the retained data does not provide a governed violation-severity definition and
the project has not validated the score against real safety outcomes.

### Keep `0000000` as a building because it is seven digits

Rejected because a syntactically seven-digit placeholder is not a valid building identity. It
would combine unrelated source records and dominate the priority queue.

### Raise or bypass the Snowflake resource monitor

Rejected because the monitor is a deliberate cost boundary. The correction remains visible as a
pending rebuild rather than expanding spending authority without user approval.
