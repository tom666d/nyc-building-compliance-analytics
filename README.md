# NYC Building Compliance & Permit Analytics Platform

An analytics engineering portfolio project that turns fragmented NYC Department of Buildings (DOB) permit, complaint, and violation records into documented, tested, building-level decision products.

## Business outcome

Operations and compliance users should be able to answer, without reconciling multiple portals:

- Which buildings have the highest unresolved compliance workload?
- Where are complaints or violations accumulating?
- How long do permits and complaints take to move through their lifecycles?
- Which definitions power each KPI, and when was the source last refreshed?

Owner-private live preview: [NYC Building Compliance 360](https://nyc-building-compliance-360-portfolio.hsieh203.chatgpt.site).
The audience remains private until an explicit sharing decision is made.

The governed analytical foundation is `fct_building_compliance_daily`, a daily building
snapshot designed for business intelligence. Three consumption marts turn that foundation into
an overview, borough comparison, and building review queue, while event-level facts remain
available for drill-through.

## Architecture

```text
NYC Open Data (Socrata APIs)
        |
        v
Python ingestion -> Snowflake RAW (JSON + ingestion metadata)
        |
        v
dbt staging -> conformed intermediate models -> dimensional marts
        |                         |             |
        +-> tests, docs, lineage  +-> quality   +-> consumption marts
                                                        |
                                                        v
                                          validated JSON snapshot -> dashboard

Airflow schedules ingestion + dbt; GitHub Actions validates every change.
```

## Quick start

1. Install the project: `make install`.
2. Download bounded real-data samples without Snowflake: `make extract-samples`.
3. Inspect the JSON Lines files and manifests under `work/samples/`.
4. Copy `.env.example` to `.env` and enter a Snowflake service account.
5. Create Snowflake objects with `infrastructure/snowflake/bootstrap.sql` as an administrator.
6. Assign the three project roles using `infrastructure/snowflake/grant_roles.example.sql`.
7. Validate role access without changing data: `make snowflake-check`.
8. Load a small real-data slice: `make ingest-sample`.
9. Build and test: `make dbt-build`.
10. Check source recency: `make dbt-freshness`.
11. Generate lineage and documentation: `make dbt-docs`.
12. Enforce physical documentation coverage: `make dbt-docs-check`.
13. Install the isolated local Airflow runtime: `make airflow-install`.
14. Validate the Dag structure without external writes: `make airflow-check`.
15. Execute a bounded live integration run: `make airflow-test-dag`.
16. Start the local Airflow interface when needed: `make airflow-standalone`.
17. Run the complete credential-free CI equivalent locally: `make ci-local`.
18. Install the locked dashboard dependencies: `make dashboard-install`.
19. Validate the dashboard data contract, production packages, lint, and build: `make dashboard-check`.
20. Start the local dashboard: `make dashboard-dev`.
21. When Snowflake capacity is available, refresh the snapshot: `make dashboard-export`.

The ingestion CLI and Airflow Dag default to bounded samples so a reviewer can run them
cheaply. Pagination is implemented; validated incremental date watermarks and late-arriving
record handling remain explicit production follow-up work.

## Phase 1 deliverables

- [從零學習路線](docs/learning/README.md)
- [Step 1：定義商業問題與成功標準](docs/learning/step-01-business-problem.md)
- [Step 2：認識 NYC Open Data 與原始資料](docs/learning/step-02-nyc-open-data.md)
- [Step 3：理解 Git、repository 與專案目錄](docs/learning/step-03-git-and-repository.md)
- [Step 4：用 Python 取得第一批真實資料](docs/learning/step-04-python-extraction.md)
- [Step 5：建立 Snowflake 資料倉儲基礎](docs/learning/step-05-snowflake-foundation.md)
- [Step 5.5：安全連線與第一次 Snowflake 真實資料載入](docs/learning/step-05-5-secure-connection-and-first-load.md)
- [Step 6：使用 dbt 建立 staging models](docs/learning/step-06-dbt-staging-models.md)
- [Step 7：建立事實表、維度表與每日快照](docs/learning/step-07-dimensional-models.md)
- [Step 8：建立資料品質測試與可觀測性](docs/learning/step-08-data-quality.md)
- [Step 9：建立文件與資料血緣](docs/learning/step-09-documentation-and-lineage.md)
- [Step 10：使用 Apache Airflow 自動執行資料管線](docs/learning/step-10-airflow-orchestration.md)
- [Step 11：使用 GitHub Actions 建立持續整合](docs/learning/step-11-github-continuous-integration.md)
- [Step 12：建立商業智慧消費層與面試展示](docs/learning/step-12-bi-consumption-layer.md)
- [Business brief](docs/business_brief.md)
- [Official source inventory and limitations](docs/data_sources.md)
- [Point-in-time source profile](docs/source_profile.md)
- [Repository structure](docs/repository_structure.md)
- [Local source extraction](docs/extraction.md)
- [Snowflake foundation and setup](docs/snowflake_setup.md)
- [Verified Snowflake deployment evidence](docs/snowflake_deployment_evidence.md)
- [dbt staging model design and evidence](docs/staging_models.md)
- [Fact grains and dimensional model](docs/data_model.md)
- [Data quality contracts and evidence](docs/data_quality.md)
- [Documentation, exposures, and end-to-end lineage](docs/lineage.md)
- [Airflow orchestration, retry safety, and verified evidence](docs/orchestration.md)
- [Continuous integration boundaries and local evidence](docs/continuous_integration.md)
- [Business intelligence consumption layer](docs/bi_consumption.md)
- [Architecture decision records](docs/decisions/)
- Executable ingestion, Snowflake, dbt, Airflow, and CI skeleton

## Portfolio development trail

Decisions are recorded before implementation in `docs/decisions`. Suggested milestone commits are documented in [CONTRIBUTING.md](CONTRIBUTING.md); small, reasoned commits are preferred over a single generated-code dump.

## Current scope

Phase 1 models DOB NOW approved permits, DOB complaints, and legacy BIS DOB violations. DOB NOW Safety Violations is deliberately deferred until a cross-system deduplication rule is profiled and validated. This limitation is visible rather than hidden.

The Snowflake foundation, key-pair service authentication, bounded real-data ingestion,
three staging views, one conformed building dimension, three event facts, an incremental
daily snapshot, and four quality audit views were verified in a real trial account on
2026-09-20. A complete nine-task Airflow run then ingested 1,000 records from each source,
passed all three freshness checks, and completed 115 data tests with zero warnings and zero
errors. The generated catalog also verified descriptions for all 118 published mart columns
and all 15 physical source columns; relation and column descriptions were persisted to
Snowflake for every published mart. Airflow remains paused by default, and the current
bounded extraction is not presented as a full production incremental strategy. Credential-free
continuous integration now validates Python, dbt parsing, the nine-task Airflow contract, and
workflow security policy. Step 12 adds three governed consumption marts and a responsive dashboard
whose checked-in snapshot is explicitly limited to 1,000 records from each source. The first live
consumption build created all three marts and passed 18 selected data tests. Dashboard review then
found and removed the source placeholder `0000000` from building identity; the corrected local
snapshot is validated, while the corresponding Snowflake rebuild remains pending the resource
monitor reset. The credential-free local suite now also audits production website dependencies,
validates dashboard rollups, lints the application, and produces an optimized build.
The project is published in the public
[GitHub repository](https://github.com/tom666d/nyc-building-compliance-analytics). Its first
corrected hosted [CI run](https://github.com/tom666d/nyc-building-compliance-analytics/actions/runs/35674860951)
passed on 2026-09-21. Branch protection and the protected Snowflake integration environment are
still separate follow-up controls and are not presented as configured.
