import argparse
import json
import sys
from typing import Any

import snowflake.connector
from dotenv import load_dotenv

from .snowflake import (
    WORKLOAD_SETTINGS,
    SnowflakeConfigurationError,
    connection_from_env,
)

EXPECTED_RAW_TABLES = {
    "RAW_DOB_COMPLAINTS",
    "RAW_DOB_NOW_PERMITS",
    "RAW_DOB_VIOLATIONS",
}
EXPECTED_SCHEMAS = {
    "loader": {"RAW"},
    "transformer": {"RAW", "DEV", "DEV_STAGING", "DEV_INTERMEDIATE", "DEV_MARTS"},
    "reader": {"DEV_MARTS"},
}


def _rows_as_dicts(cursor) -> list[dict[str, Any]]:
    columns = [column[0].lower() for column in cursor.description]
    return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]


def inspect_connection(connection, workload: str) -> dict[str, Any]:
    """Run read-only checks and return a secret-free summary."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), "
            "CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA()"
        )
        context = cursor.fetchone()

        cursor.execute("SHOW SCHEMAS IN DATABASE NYC_DOB_ANALYTICS")
        visible_schemas = {row["name"] for row in _rows_as_dicts(cursor)}

        visible_raw_tables: set[str] = set()
        if workload in {"loader", "transformer"} and "RAW" in visible_schemas:
            cursor.execute("SHOW TABLES IN SCHEMA NYC_DOB_ANALYTICS.RAW")
            visible_raw_tables = {row["name"] for row in _rows_as_dicts(cursor)}

    missing_schemas = EXPECTED_SCHEMAS[workload] - visible_schemas
    missing_raw_tables = (
        EXPECTED_RAW_TABLES - visible_raw_tables
        if workload in {"loader", "transformer"}
        else set()
    )
    return {
        "account": context[0],
        "user": context[1],
        "role": context[2],
        "warehouse": context[3],
        "database": context[4],
        "schema": context[5],
        "workload": workload,
        "visible_schemas": sorted(visible_schemas),
        "visible_raw_tables": sorted(visible_raw_tables),
        "missing_schemas": sorted(missing_schemas),
        "missing_raw_tables": sorted(missing_raw_tables),
        "ready": not missing_schemas and not missing_raw_tables,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check a Snowflake role and project objects without changing data"
    )
    parser.add_argument("workload", choices=sorted(WORKLOAD_SETTINGS))
    return parser.parse_args()


def main() -> int:
    load_dotenv()
    args = parse_args()
    try:
        with connection_from_env(args.workload) as connection:
            result = inspect_connection(connection, args.workload)
    except SnowflakeConfigurationError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except snowflake.connector.Error as exc:
        print(f"Snowflake connection check failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
