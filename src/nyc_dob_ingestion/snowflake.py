import os
from collections.abc import Mapping
from typing import Any

import snowflake.connector

WORKLOAD_SETTINGS = {
    "loader": ("SNOWFLAKE_INGEST_ROLE", "NYC_DOB_LOADER", "RAW"),
    "transformer": ("SNOWFLAKE_DBT_ROLE", "NYC_DOB_TRANSFORMER", "DEV"),
    "reader": ("SNOWFLAKE_READER_ROLE", "NYC_DOB_READER", "DEV_MARTS"),
}


class SnowflakeConfigurationError(ValueError):
    """Raised when local Snowflake connection settings are incomplete."""


def connection_parameters_from_env(
    workload: str,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Build connector arguments without logging or returning secrets separately."""
    if workload not in WORKLOAD_SETTINGS:
        expected = ", ".join(sorted(WORKLOAD_SETTINGS))
        raise SnowflakeConfigurationError(
            f"Unknown workload {workload!r}; expected one of: {expected}"
        )

    values = os.environ if environ is None else environ
    required = ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD")
    missing = [name for name in required if not values.get(name, "").strip()]
    if missing:
        raise SnowflakeConfigurationError(
            "Missing required environment variables: " + ", ".join(missing)
        )

    role_variable, default_role, default_schema = WORKLOAD_SETTINGS[workload]
    schema = (
        values.get("SNOWFLAKE_SCHEMA", default_schema).strip() or default_schema
        if workload == "transformer"
        else default_schema
    )
    return {
        "account": values["SNOWFLAKE_ACCOUNT"].strip(),
        "user": values["SNOWFLAKE_USER"].strip(),
        "password": values["SNOWFLAKE_PASSWORD"],
        "role": values.get(role_variable, default_role).strip() or default_role,
        "warehouse": values.get("SNOWFLAKE_WAREHOUSE", "NYC_DOB_WH").strip()
        or "NYC_DOB_WH",
        "database": values.get("SNOWFLAKE_DATABASE", "NYC_DOB_ANALYTICS").strip()
        or "NYC_DOB_ANALYTICS",
        "schema": schema,
    }


def connection_from_env(workload: str):
    return snowflake.connector.connect(**connection_parameters_from_env(workload))
