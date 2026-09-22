.PHONY: install test lint ci-workflow-check ci-local extract-samples snowflake-check ingest-sample dbt-debug dbt-deps dbt-parse dbt-build dbt-freshness dbt-docs dbt-docs-check dashboard-export dashboard-install dashboard-check dashboard-dev airflow-install airflow-check airflow-init airflow-test-dag airflow-standalone

AIRFLOW_VERSION := 3.3.2
AIRFLOW_PYTHON_VERSION := $(shell python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
AIRFLOW_CONSTRAINT_URL := https://raw.githubusercontent.com/apache/airflow/constraints-$(AIRFLOW_VERSION)/constraints-$(AIRFLOW_PYTHON_VERSION).txt
AIRFLOW_ENV := AIRFLOW_HOME=$(CURDIR)/.airflow AIRFLOW__CORE__DAGS_FOLDER=$(CURDIR)/airflow/dags AIRFLOW__CORE__LOAD_EXAMPLES=False NYC_DOB_PROJECT_ROOT=$(CURDIR)
DASHBOARD_NPM_CACHE := $(CURDIR)/.npm-cache
DOTENV_RUN := $(if $(wildcard .env),.venv/bin/dotenv run -- ,)

install:
	python3 -m venv .venv
	.venv/bin/pip install --editable '.[dev]'

test:
	.venv/bin/pytest

lint:
	.venv/bin/ruff check src tests airflow scripts

ci-workflow-check:
	.venv/bin/python scripts/check_ci_workflows.py

ci-local: lint test ci-workflow-check dbt-deps dbt-parse airflow-check dashboard-install dashboard-check
	.airflow-venv/bin/pip check
	.venv/bin/pip check

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
	$(DOTENV_RUN).venv/bin/dbt deps --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-debug:
	$(DOTENV_RUN).venv/bin/dbt debug --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-parse:
	$(DOTENV_RUN).venv/bin/dbt parse --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-build:
	$(DOTENV_RUN).venv/bin/dbt build --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-freshness:
	$(DOTENV_RUN).venv/bin/dbt source freshness --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-docs:
	$(DOTENV_RUN).venv/bin/dbt docs generate --project-dir dbt/nyc_building_compliance --profiles-dir dbt/nyc_building_compliance

dbt-docs-check: dbt-docs
	.venv/bin/python scripts/check_dbt_documentation.py

dashboard-export:
	PYTHONPATH=src .venv/bin/dotenv run -- .venv/bin/python scripts/export_dashboard_data.py

dashboard-install:
	cd dashboard && NPM_CONFIG_CACHE=$(DASHBOARD_NPM_CACHE) npm ci

dashboard-check:
	cd dashboard && NPM_CONFIG_CACHE=$(DASHBOARD_NPM_CACHE) npm audit --omit=dev
	cd dashboard && NPM_CONFIG_CACHE=$(DASHBOARD_NPM_CACHE) npm test
	cd dashboard && NPM_CONFIG_CACHE=$(DASHBOARD_NPM_CACHE) npm run build

dashboard-dev:
	cd dashboard && NPM_CONFIG_CACHE=$(DASHBOARD_NPM_CACHE) npm run dev

.airflow-venv/.installed: pyproject.toml Makefile
	python3 -m venv .airflow-venv
	.airflow-venv/bin/pip install "apache-airflow==$(AIRFLOW_VERSION)" "apache-airflow-providers-standard>=1.10,<2" --constraint "$(AIRFLOW_CONSTRAINT_URL)"
	.airflow-venv/bin/pip check
	touch .airflow-venv/.installed

airflow-install: .airflow-venv/.installed

airflow-check: airflow-install
	$(AIRFLOW_ENV) .airflow-venv/bin/python scripts/check_airflow_dag.py

airflow-init: airflow-install
	mkdir -p .airflow
	$(AIRFLOW_ENV) .airflow-venv/bin/airflow db migrate

airflow-test-dag: airflow-init
	.venv/bin/dotenv run -- env $(AIRFLOW_ENV) .airflow-venv/bin/airflow dags test nyc_dob_daily 2026-09-20 --dagfile-path $(CURDIR)/airflow/dags/nyc_dob_pipeline.py

airflow-standalone: airflow-install
	.venv/bin/dotenv run -- env $(AIRFLOW_ENV) .airflow-venv/bin/airflow standalone
