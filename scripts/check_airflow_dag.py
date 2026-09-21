"""Load the Airflow Dag and enforce its operational structure without running tasks."""

from __future__ import annotations

import os
from pathlib import Path

from airflow.dag_processing.dagbag import DagBag

EXPECTED_DEPENDENCIES = {
    "verify_loader_access": {
        "ingest_sources.permits",
        "ingest_sources.complaints",
        "ingest_sources.violations",
    },
    "verify_transformer_access": {
        "ingest_sources.permits",
        "ingest_sources.complaints",
        "ingest_sources.violations",
    },
    "ingest_sources.permits": {"check_source_freshness"},
    "ingest_sources.complaints": {"check_source_freshness"},
    "ingest_sources.violations": {"check_source_freshness"},
    "check_source_freshness": {"build_and_test"},
    "build_and_test": {"generate_documentation"},
    "generate_documentation": {"validate_documentation"},
    "validate_documentation": set(),
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    project_root = Path(
        os.getenv("NYC_DOB_PROJECT_ROOT", Path(__file__).resolve().parents[1])
    ).resolve()
    dag_folder = project_root / "airflow" / "dags"
    dag_bag = DagBag(dag_folder=str(dag_folder))

    _require(not dag_bag.import_errors, f"Dag import errors: {dag_bag.import_errors}")
    dag = dag_bag.dags.get("nyc_dob_daily")
    _require(dag is not None, "nyc_dob_daily was not found")

    _require(set(dag.task_dict) == set(EXPECTED_DEPENDENCIES), "Unexpected task set")
    for task_id, expected_downstream in EXPECTED_DEPENDENCIES.items():
        actual_downstream = dag.get_task(task_id).downstream_task_ids
        _require(
            actual_downstream == expected_downstream,
            f"{task_id} downstream mismatch: {actual_downstream}",
        )

    _require(dag.catchup is False, "Historical catchup must remain disabled")
    _require(dag.max_active_runs == 1, "Only one active Dag run is allowed")
    _require(dag.is_paused_upon_creation is True, "The Dag must be paused on first creation")
    _require(str(dag.timezone) == "America/New_York", "Dag timezone must follow NYC")
    _require(
        getattr(dag.timetable, "expression", None) == "0 6 * * *",
        "Expected a daily 06:00 schedule",
    )

    for task in dag.tasks:
        _require(task.retries == 2, f"{task.task_id} must inherit two retries")
        _require(task.execution_timeout is not None, f"{task.task_id} needs a timeout")

    for dataset in ("permits", "complaints", "violations"):
        task = dag.get_task(f"ingest_sources.{dataset}")
        _require(f"nyc-dob-ingest {dataset}" in task.bash_command, f"Wrong {dataset} command")
        _require("--load-id" in task.bash_command, f"{dataset} is not retry-safe")
        _require(task.env["NYC_DOB_LOAD_ID"] == "{{ run_id }}", "Run ID is not templated")

    print("Airflow Dag contract passed.")
    print(f"  dag_id: {dag.dag_id}")
    print(f"  tasks: {len(dag.tasks)}")
    print(f"  schedule: {dag.timetable.expression} ({dag.timezone})")
    print("  catchup: disabled")
    print("  max active runs: 1")
    print("  paused on creation: yes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
