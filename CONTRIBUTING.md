# Development workflow

Use feature branches and small commits whose messages explain intent. A credible initial history might be:

1. `docs: define users, decisions, and source boundaries`
2. `feat: add idempotent Socrata ingestion`
3. `feat: model conformed DOB facts and building dimension`
4. `test: add keys, relationships, and business-rule assertions`
5. `docs: document published models and downstream lineage`
6. `test: enforce documentation coverage against the catalog`
7. `feat: orchestrate the verified analytics pipeline`
8. `docs: explain Airflow orchestration decisions`
9. `ci: validate Python, dbt, and Airflow changes`

For every material modeling choice, add or update an ADR. Pull requests should include the business question, grain impact, test evidence, and any coverage change.

For orchestration changes, include the Dag structural check and state whether a live
integration run was performed. Do not imply that a local SQLite Airflow deployment or a
bounded source slice is production infrastructure.

Do not commit `.env`, Snowflake credentials, raw exports, `target/`, dbt logs,
`.airflow-venv/`, or `.airflow/` runtime state.
