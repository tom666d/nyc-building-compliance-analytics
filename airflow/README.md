# Airflow local runtime

The `nyc_dob_daily` Dag coordinates existing project commands. Read
[`docs/orchestration.md`](../docs/orchestration.md) for the task graph, retry-safety design,
verified evidence, and production limitations.

## Safe first check

```text
make install
make airflow-install
make airflow-check
```

The structural check imports the Dag and validates its tasks, dependencies, schedule,
timeouts, retry policy, concurrency, and paused initial state without calling NYC Open Data
or Snowflake.

## Live integration run

```text
make airflow-test-dag
```

This command uses the ignored `.env` credentials, reads live official data, writes bounded
raw snapshots to Snowflake, builds the dbt project, runs its tests, and validates generated
documentation.

## Local interface

```text
make airflow-standalone
```

Local Airflow state is written under ignored `.airflow/`. The separate ignored
`.airflow-venv/` contains the constrained Airflow installation. The Dag begins paused so
opening the interface cannot silently authorize a recurring Snowflake workload.
