.PHONY: install test lint extract-samples snowflake-check ingest-sample dbt-deps dbt-parse dbt-build dbt-docs

install:
	python3 -m venv .venv
	.venv/bin/pip install '.[dev]'

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check src tests airflow

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
	cd dbt/nyc_building_compliance && ../../.venv/bin/dbt deps

dbt-parse:
	cd dbt/nyc_building_compliance && ../../.venv/bin/dbt parse --profiles-dir .

dbt-build:
	cd dbt/nyc_building_compliance && ../../.venv/bin/dbt build --profiles-dir .

dbt-docs:
	cd dbt/nyc_building_compliance && ../../.venv/bin/dbt docs generate --profiles-dir .
