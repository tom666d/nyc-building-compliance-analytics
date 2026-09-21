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
10. `docs: explain continuous integration boundaries`

For every material modeling choice, add or update an ADR. Pull requests should include the business question, grain impact, test evidence, and any coverage change.

For orchestration changes, include the Dag structural check and state whether a live
integration run was performed. Do not imply that a local SQLite Airflow deployment or a
bounded source slice is production infrastructure.

Before proposing a change, run `make ci-local`. It is the local equivalent of the
credential-free GitHub workflow and covers linting, Python tests, workflow policy, dbt parsing,
Airflow structure, and dependency consistency. A live Snowflake build is a separate, explicitly
authorized integration check because it changes development relations and consumes credits.

After the repository is published, protect `main` and require the static CI status check. Do not
enable automatic warehouse access for pull-request code until a dedicated CI role and isolated
per-change schema strategy exist.

Do not commit `.env`, Snowflake credentials, raw exports, `target/`, dbt logs,
`.airflow-venv/`, or `.airflow/` runtime state.
