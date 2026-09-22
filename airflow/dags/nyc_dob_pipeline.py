"""Daily orchestration for the NYC Building Compliance analytics platform."""

from __future__ import annotations

import os
import shlex
from datetime import timedelta
from pathlib import Path

import pendulum
from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG, TaskGroup

DAG_ID = "nyc_dob_daily"
DATASETS = ("permits", "complaints", "violations")


def _positive_integer_environment(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        value = int(raw_value)
    except ValueError as error:
        raise ValueError(f"{name} must be a positive integer") from error
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


PROJECT_ROOT = Path(
    os.getenv("NYC_DOB_PROJECT_ROOT", Path(__file__).resolve().parents[2])
).resolve()
PROJECT_VENV_BIN = PROJECT_ROOT / ".venv" / "bin"
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt" / "nyc_building_compliance"
INGEST_LIMIT = _positive_integer_environment("AIRFLOW_NYC_DOB_INGEST_LIMIT", 1_000)

INGEST_EXECUTABLE = shlex.quote(str(PROJECT_VENV_BIN / "nyc-dob-ingest"))
SNOWFLAKE_CHECK_EXECUTABLE = shlex.quote(
    str(PROJECT_VENV_BIN / "nyc-dob-snowflake-check")
)
DOTENV_EXECUTABLE = shlex.quote(str(PROJECT_VENV_BIN / "dotenv"))
DBT_EXECUTABLE = shlex.quote(str(PROJECT_VENV_BIN / "dbt"))
PYTHON_EXECUTABLE = shlex.quote(str(PROJECT_VENV_BIN / "python"))
DBT_PROJECT_ARGUMENTS = (
    f"--project-dir {shlex.quote(str(DBT_PROJECT_DIR))} "
    f"--profiles-dir {shlex.quote(str(DBT_PROJECT_DIR))}"
)

DOCUMENTATION = """
### NYC Department of Buildings daily analytics pipeline

This Dag coordinates existing ingestion and transformation commands; business logic remains
inside the Python ingestion package and dbt project.

1. Validate least-privilege Snowflake loader and transformer access.
2. Ingest bounded real records from permits, complaints, and violations in parallel.
3. Stop if any official source is stale.
4. Build all dbt models and execute their data-quality contracts.
5. Generate the dbt catalog and enforce complete published documentation.

The Dag is paused when first created to prevent unapproved Snowflake usage. The same Airflow
run identifier is passed to every ingestion task so task retries do not duplicate raw rows.
"""

DEFAULT_ARGS = {
    "owner": "analytics-engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

with DAG(
    dag_id=DAG_ID,
    description="Ingest, test, document, and publish NYC DOB compliance data",
    doc_md=DOCUMENTATION,
    start_date=pendulum.datetime(2026, 1, 1, tz="America/New_York"),
    schedule="0 6 * * *",
    catchup=False,
    is_paused_upon_creation=True,
    max_active_runs=1,
    dagrun_timeout=timedelta(hours=2),
    default_args=DEFAULT_ARGS,
    tags=["data-product", "nyc-dob", "analytics-engineering"],
) as dag:
    verify_loader_access = BashOperator(
        task_id="verify_loader_access",
        bash_command=f"set -euo pipefail\n{SNOWFLAKE_CHECK_EXECUTABLE} loader",
        cwd=str(PROJECT_ROOT),
        append_env=True,
        do_xcom_push=False,
        execution_timeout=timedelta(minutes=5),
        doc_md="Verify that the loader role can see the raw tables before changing data.",
    )

    verify_transformer_access = BashOperator(
        task_id="verify_transformer_access",
        bash_command=f"set -euo pipefail\n{SNOWFLAKE_CHECK_EXECUTABLE} transformer",
        cwd=str(PROJECT_ROOT),
        append_env=True,
        do_xcom_push=False,
        execution_timeout=timedelta(minutes=5),
        doc_md="Verify dbt's transformer role and schemas before ingestion begins.",
    )

    with TaskGroup(
        group_id="ingest_sources",
        tooltip="Bounded, retry-safe ingestion from official NYC Open Data APIs",
    ) as ingest_sources:
        for dataset in DATASETS:
            BashOperator(
                task_id=dataset,
                bash_command=(
                    "set -euo pipefail\n"
                    f"{INGEST_EXECUTABLE} {dataset} "
                    '--limit "$NYC_DOB_INGEST_LIMIT" '
                    '--page-size 1000 --load-id "$NYC_DOB_LOAD_ID"'
                ),
                cwd=str(PROJECT_ROOT),
                env={
                    "NYC_DOB_INGEST_LIMIT": str(INGEST_LIMIT),
                    "NYC_DOB_LOAD_ID": "{{ run_id }}",
                },
                append_env=True,
                do_xcom_push=False,
                execution_timeout=timedelta(minutes=20),
                doc_md=(
                    f"Load a bounded slice of official `{dataset}` data. A stable run ID "
                    "makes retries idempotent."
                ),
            )

    check_source_freshness = BashOperator(
        task_id="check_source_freshness",
        bash_command=(
            "set -euo pipefail\n"
            f"{DOTENV_EXECUTABLE} run -- {DBT_EXECUTABLE} source freshness "
            f"{DBT_PROJECT_ARGUMENTS}"
        ),
        cwd=str(PROJECT_ROOT),
        append_env=True,
        do_xcom_push=False,
        execution_timeout=timedelta(minutes=10),
        doc_md="Stop the workflow if the raw source timestamps violate the freshness policy.",
    )

    build_and_test = BashOperator(
        task_id="build_and_test",
        bash_command=(
            "set -euo pipefail\n"
            f"{DOTENV_EXECUTABLE} run -- {DBT_EXECUTABLE} build {DBT_PROJECT_ARGUMENTS}"
        ),
        cwd=str(PROJECT_ROOT),
        append_env=True,
        do_xcom_push=False,
        execution_timeout=timedelta(minutes=45),
        doc_md="Build the transformation graph and execute all dbt data-quality contracts.",
    )

    generate_documentation = BashOperator(
        task_id="generate_documentation",
        bash_command=(
            "set -euo pipefail\n"
            f"{DOTENV_EXECUTABLE} run -- {DBT_EXECUTABLE} docs generate "
            f"{DBT_PROJECT_ARGUMENTS}"
        ),
        cwd=str(PROJECT_ROOT),
        append_env=True,
        do_xcom_push=False,
        execution_timeout=timedelta(minutes=15),
        doc_md="Regenerate dbt lineage and physical Snowflake catalog metadata.",
    )

    validate_documentation = BashOperator(
        task_id="validate_documentation",
        bash_command=(
            "set -euo pipefail\n"
            f"{PYTHON_EXECUTABLE} scripts/check_dbt_documentation.py"
        ),
        cwd=str(PROJECT_ROOT),
        append_env=True,
        do_xcom_push=False,
        execution_timeout=timedelta(minutes=5),
        doc_md="Fail publication if physical marts, sources, or exposures lack documentation.",
    )

    for preflight_task in (verify_loader_access, verify_transformer_access):
        preflight_task >> ingest_sources

    (
        ingest_sources
        >> check_source_freshness
        >> build_and_test
        >> generate_documentation
        >> validate_documentation
    )
