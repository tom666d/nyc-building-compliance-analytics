# Development workflow

Use feature branches and small commits whose messages explain intent. A credible initial history might be:

1. `docs: define users, decisions, and source boundaries`
2. `feat: add idempotent Socrata ingestion`
3. `feat: model conformed DOB facts and building dimension`
4. `test: add keys, relationships, and business-rule assertions`
5. `docs: document published models and downstream lineage`
6. `test: enforce documentation coverage against the catalog`
7. `ci: validate Python and dbt changes`

For every material modeling choice, add or update an ADR. Pull requests should include the business question, grain impact, test evidence, and any coverage change.

Do not commit `.env`, Snowflake credentials, raw exports, `target/`, or dbt logs.
