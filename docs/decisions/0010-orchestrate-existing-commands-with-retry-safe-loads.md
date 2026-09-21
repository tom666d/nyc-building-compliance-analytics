# ADR 0010: Orchestrate existing commands with retry-safe bounded loads

- Status: Accepted
- Date: 2026-09-20

## Context

The ingestion package, Snowflake access checks, dbt build, source freshness check, and
documentation contract already existed as independently executable commands. Scheduling
them with an operating-system timer would not provide a single dependency graph, task-level
retries, execution history, or a visible distinction between extraction, transformation,
quality, and publication failures.

Airflow retries also introduce a data risk. A task may commit some raw rows and fail before
Airflow receives a successful exit status. Repeating a plain insert would duplicate those
rows. The portfolio account also requires explicit limits so a scheduling mistake does not
consume unbounded Snowflake credits.

## Decision

Use one Apache Airflow Dag to coordinate existing command-line interfaces rather than move
business logic into orchestration code.

The Dag will:

1. run least-privilege role checks before any data change;
2. keep the three source ingestion tasks independent so a scheduler can run them in parallel;
3. use the Airflow run identifier as a stable raw `load_id`;
4. merge raw rows on `(source_row_hash, load_id)` in batches;
5. require source freshness, dbt build and data tests, documentation generation, and the
   documentation contract to pass in that order;
6. disable catch-up, permit one active run, and start paused;
7. default to 1,000 records per source until incremental watermarks are designed;
8. install Airflow in an isolated constrained environment while executing project commands
   from the normal project environment.

## Consequences

### Benefits

- One graph records the full data-product publication path and the exact failing stage.
- Existing commands remain directly testable and are not coupled to Airflow internals.
- Retries of the same run do not duplicate raw payloads.
- Source tasks can run concurrently under a normal executor.
- Freshness, data quality, and documentation become blocking publication gates.
- Paused initialization, bounded loads, and single-run concurrency reduce trial-account risk.

### Costs and limitations

- A second Python environment must be maintained for Airflow.
- Daily runs preserve repeated source snapshots; this is audit-friendly but not yet a
  full-volume retention strategy.
- The current local SQLite deployment is suitable for learning and integration evidence,
  not production availability.
- BashOperator exposes process boundaries clearly but provides less Airflow-native metadata
  than provider-specific operators.
- Incremental source filtering and late-arriving data policy remain future work.

## Alternatives considered

### Put Python and SQL business logic directly in the Dag file

Rejected because orchestration code would become difficult to test without Airflow and
would duplicate logic already owned by the ingestion package and dbt.

### Use plain inserts and rely on Airflow retries being rare

Rejected because retries are a normal recovery mechanism. A partial commit must not turn a
temporary failure into corrupted duplicate data.

### Use a local cron job

Rejected because it would hide task-level dependencies, retries, quality gates, and run
history that are central to the portfolio objective.

### Enable an unbounded daily load immediately

Rejected because the current project has not yet validated incremental watermarks or the
cost profile of full-volume extraction. A visible bound is more credible than implying
production readiness without evidence.
