.PHONY: install test lint ingest-sample dbt-deps dbt-parse dbt-build dbt-docs

install:
	python3 -m venv .venv
	.venv/bin/pip install -e '.[dev]'

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check src tests airflow

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
