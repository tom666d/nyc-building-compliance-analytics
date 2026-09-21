.PHONY: install test lint extract-samples snowflake-check ingest-sample dbt-debug dbt-deps dbt-parse dbt-build dbt-freshness dbt-docs dbt-docs-check

install:
	python3 -m venv .venv
	.venv/bin/pip install '.[dev]'

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check src tests airflow scripts

extract-samples:
	.venv/bin/nyc-dob-extract permits --limit 25
	.venv/bin/nyc-dob-extract complaints --limit 25
	.venv/bin/nyc-dob-extract violations --limit 25

snowflake-check:
	.venv/bin/nyc-dob-snowflake-check loader
	.venv/bin/nyc-dob-snowflake-check transformer
	.venv/bin/nyc-dob-snowflake-check reader

ingest-sample:
	.venv/bin/nyc-dob-ingest --all --limit 1000

dbt-deps:
	.venv/bin/dotenv run -- .venv/bin/dbt deps --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-debug:
	.venv/bin/dotenv run -- .venv/bin/dbt debug --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-parse:
	.venv/bin/dotenv run -- .venv/bin/dbt parse --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-build:
	.venv/bin/dotenv run -- .venv/bin/dbt build --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-freshness:
	.venv/bin/dotenv run -- .venv/bin/dbt source freshness --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-docs:
	.venv/bin/dotenv run -- .venv/bin/dbt docs generate --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-docs-check: dbt-docs
	.venv/bin/python scripts/check_dbt_documentation.py
