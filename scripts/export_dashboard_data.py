"""Export a small, credential-free dashboard snapshot from governed Snowflake marts."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from nyc_dob_ingestion.snowflake import connection_from_env

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "dashboard" / "data" / "dashboard-snapshot.json"
RUN_RESULTS = (
    PROJECT_ROOT
    / "dbt"
    / "nyc_building_compliance"
    / "target"
    / "run_results.json"
)

OVERVIEW_SQL = "select * from mart_compliance_overview"
BOROUGH_SQL = """
select *
from mart_borough_compliance_current
order by priority_building_rate_pct desc, borough
"""
ATTENTION_TIER_SQL = """
select attention_tier, count(*) as building_count
from mart_building_compliance_current
group by attention_tier
order by case attention_tier
  when 'CRITICAL' then 1 when 'HIGH' then 2 when 'MODERATE' then 3 else 4 end
"""
PRIORITY_BUILDING_SQL = """
select
  bin,
  borough,
  display_address,
  open_complaint_count,
  open_violation_count,
  total_open_compliance_item_count,
  oldest_open_item_age_days,
  attention_score,
  attention_tier
from mart_building_compliance_current
where total_open_compliance_item_count > 0
order by attention_score desc, total_open_compliance_item_count desc, bin
limit 50
"""
QUALITY_SQL = """
select domain, total_record_count, building_key_coverage_pct, quality_status
from audit_data_quality_summary
order by domain
"""

FIELD_NAMES = {
    "snapshot_date": "snapshotDate",
    "observed_building_count": "observedBuildingCount",
    "building_with_open_item_count": "buildingWithOpenItemCount",
    "priority_building_count": "priorityBuildingCount",
    "priority_building_rate_pct": "priorityBuildingRatePct",
    "open_complaint_count": "openComplaintCount",
    "open_violation_count": "openViolationCount",
    "active_permit_record_count": "activePermitRecordCount",
    "total_open_compliance_item_count": "totalOpenComplianceItemCount",
    "highest_attention_score": "highestAttentionScore",
    "median_complaint_resolution_days_12m": "medianComplaintResolutionDays12m",
    "resolved_complaint_count_12m": "resolvedComplaintCount12m",
    "attention_tier": "attentionTier",
    "building_count": "buildingCount",
    "display_address": "displayAddress",
    "oldest_open_item_age_days": "oldestOpenItemAgeDays",
    "attention_score": "attentionScore",
    "total_record_count": "totalRecordCount",
    "building_key_coverage_pct": "buildingKeyCoveragePct",
    "quality_status": "qualityStatus",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export governed dashboard data without publishing Snowflake credentials"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _rows(cursor, statement: str) -> list[dict[str, Any]]:
    cursor.execute(statement)
    columns = [column[0].lower() for column in cursor.description]
    return [
        {
            FIELD_NAMES.get(column, column): _json_value(value)
            for column, value in zip(columns, row, strict=True)
        }
        for row in cursor.fetchall()
    ]


def _build_evidence() -> dict[str, int]:
    if not RUN_RESULTS.exists():
        return {"modelsBuilt": 0, "checksPassed": 0, "warnings": 0, "errors": 0}
    results = json.loads(RUN_RESULTS.read_text()).get("results", [])
    statuses = [result.get("status", "") for result in results]
    return {
        "modelsBuilt": sum(
            result.get("unique_id", "").startswith("model.")
            and result.get("status") == "success"
            for result in results
        ),
        "checksPassed": sum(status in {"pass", "success"} for status in statuses),
        "warnings": sum(status == "warn" for status in statuses),
        "errors": sum(status in {"error", "fail"} for status in statuses),
    }


def export_snapshot(connection) -> dict[str, Any]:
    with connection.cursor() as cursor:
        overview = _rows(cursor, OVERVIEW_SQL)[0]
        boroughs = _rows(cursor, BOROUGH_SQL)
        attention_tiers = _rows(cursor, ATTENTION_TIER_SQL)
        priority_buildings = _rows(cursor, PRIORITY_BUILDING_SQL)
        quality = _rows(cursor, QUALITY_SQL)

    source_records = {
        "permits" if row["domain"] == "permit_records" else row["domain"]: row[
            "totalRecordCount"
        ]
        for row in quality
    }
    return {
        "metadata": {
            "exportedOn": datetime.now(UTC).date().isoformat(),
            "snapshotDate": overview["snapshotDate"],
            "scope": (
                "Bounded validation sample sourced from three official NYC Open Data "
                "datasets. Results are not citywide population estimates."
            ),
            "normalizationNote": (
                "Zero and borough-zero placeholder BIN values are excluded from the "
                "conformed building identity."
            ),
            "sourceRecords": source_records,
            "buildEvidence": _build_evidence(),
        },
        "overview": overview,
        "attentionTiers": attention_tiers,
        "boroughs": boroughs,
        "priorityBuildings": priority_buildings,
        "quality": quality,
    }


def write_snapshot(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=output_path.parent, prefix=f".{output_path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w") as handle:
            json.dump(payload, handle, indent=2, sort_keys=False)
            handle.write("\n")
        Path(temporary_name).replace(output_path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def main() -> int:
    load_dotenv()
    args = parse_args()
    with connection_from_env("reader") as connection:
        payload = export_snapshot(connection)
    write_snapshot(payload, args.output)
    print(f"Dashboard snapshot exported: {args.output}")
    print(f"  snapshot date: {payload['metadata']['snapshotDate']}")
    print(f"  priority buildings: {len(payload['priorityBuildings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
