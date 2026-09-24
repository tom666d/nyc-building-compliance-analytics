# Development workflow

Use feature branches and small commits whose messages explain intent. Each commit should contain
one independently reviewable change and its relevant tests or documentation. Commit history should
record the actual development sequence rather than being rewritten to present a predetermined path.

For every material modeling choice, add or update an ADR. Pull requests should include the business question, grain impact, test evidence, and any coverage change.

For orchestration changes, include the Dag structural check and state whether a live
integration run was performed. Do not imply that a local SQLite Airflow deployment or a
bounded source slice is production infrastructure.

Before proposing a change, run `make ci-local`. It is the local equivalent of the
credential-free GitHub workflow and covers linting, Python tests, workflow policy, dbt parsing,
Airflow structure, dashboard data and build contracts, production package auditing, and dependency
consistency. Use `make dashboard-check` when working only on the website. A live Snowflake build is
a separate, explicitly authorized integration check because it changes development relations and
consumes credits.

After the repository is published, protect `main` and require the static CI status check. Do not
enable automatic warehouse access for pull-request code until a dedicated CI role and isolated
per-change schema strategy exist.

Do not commit `.env`, Snowflake credentials, raw exports, `target/`, dbt logs,
`.airflow-venv/`, `.airflow/` runtime state, `node_modules/`, or generated dashboard build output.
