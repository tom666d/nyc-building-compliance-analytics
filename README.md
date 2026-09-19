# NYC Building Compliance & Permit Analytics Platform

An analytics engineering portfolio project that turns fragmented NYC Department of Buildings (DOB) permit, complaint, and violation records into documented, tested, building-level decision products.

## Business outcome

Operations and compliance users should be able to answer, without reconciling multiple portals:

- Which buildings have the highest unresolved compliance workload?
- Where are complaints or violations accumulating?
- How long do permits and complaints take to move through their lifecycles?
- Which definitions power each KPI, and when was the source last refreshed?

The first product is `fct_building_compliance_daily`, a daily building snapshot designed for BI. Event-level facts remain available for drill-through.

## Architecture

```text
NYC Open Data (Socrata APIs)
        |
        v
Python ingestion -> Snowflake RAW (JSON + ingestion metadata)
        |
        v
dbt staging -> conformed intermediate models -> dimensional marts
        |                                      |
        +-> tests, docs, lineage                +-> BI semantic layer

Airflow schedules ingestion + dbt; GitHub Actions validates every change.
```

## Quick start

1. Copy `.env.example` to `.env` and enter a Snowflake service account.
2. Create Snowflake objects with `infrastructure/snowflake/bootstrap.sql` as an administrator.
3. Install the project: `make install`.
4. Load a small real-data slice: `make ingest-sample`.
5. Build and test: `make dbt-build`.
6. Generate lineage and documentation: `make dbt-docs`.

The ingestion CLI defaults to bounded samples so a reviewer can run it cheaply. Production runs use the same code with date watermarks and pagination.

## Phase 1 deliverables

- [從零學習路線](docs/learning/README.md)
- [Step 1：定義商業問題與成功標準](docs/learning/step-01-business-problem.md)
- [Step 2：認識 NYC Open Data 與原始資料](docs/learning/step-02-nyc-open-data.md)
- [Step 3：理解 Git、repository 與專案目錄](docs/learning/step-03-git-and-repository.md)
- [Business brief](docs/business_brief.md)
- [Official source inventory and limitations](docs/data_sources.md)
- [Point-in-time source profile](docs/source_profile.md)
- [Repository structure](docs/repository_structure.md)
- [Fact grains and dimensional model](docs/data_model.md)
- [Architecture decision records](docs/decisions/)
- Executable ingestion, Snowflake, dbt, Airflow, and CI skeleton

## Portfolio development trail

Decisions are recorded before implementation in `docs/decisions`. Suggested milestone commits are documented in [CONTRIBUTING.md](CONTRIBUTING.md); small, reasoned commits are preferred over a single generated-code dump.

## Current scope

Phase 1 models DOB NOW approved permits, DOB complaints, and legacy BIS DOB violations. DOB NOW Safety Violations is deliberately deferred until a cross-system deduplication rule is profiled and validated. This limitation is visible rather than hidden.
