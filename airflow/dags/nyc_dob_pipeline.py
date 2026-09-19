from datetime import UTC, datetime, timedelta

from airflow.operators.bash import BashOperator

from airflow import DAG

with DAG(
    dag_id="nyc_dob_daily",
    description="Ingest and transform NYC DOB compliance datasets",
    start_date=datetime(2026, 1, 1, tzinfo=UTC),
    schedule="0 7 * * *",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=10)},
    tags=["portfolio", "nyc-dob"],
) as dag:
    ingest = BashOperator(
        task_id="ingest_open_data",
        bash_command="nyc-dob-ingest --all",
    )
    source_freshness = BashOperator(
        task_id="check_source_freshness",
        bash_command="cd $DBT_PROJECT_DIR && dbt source freshness --profiles-dir .",
    )
    build = BashOperator(
        task_id="build_and_test",
        bash_command="cd $DBT_PROJECT_DIR && dbt build --profiles-dir .",
    )
    ingest >> source_freshness >> build
