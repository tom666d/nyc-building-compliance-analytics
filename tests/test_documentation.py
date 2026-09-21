import importlib.util
import sys
from copy import deepcopy
from pathlib import Path

SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "check_dbt_documentation.py"
SPEC = importlib.util.spec_from_file_location("check_dbt_documentation", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
DOCUMENTATION_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = DOCUMENTATION_MODULE
SPEC.loader.exec_module(DOCUMENTATION_MODULE)
audit_documentation = DOCUMENTATION_MODULE.audit_documentation


def _artifacts() -> tuple[dict, dict]:
    model_id = "model.nyc_building_compliance.example_mart"
    source_id = "source.nyc_building_compliance.dob_raw.example_source"
    manifest = {
        "nodes": {
            model_id: {
                "resource_type": "model",
                "package_name": "nyc_building_compliance",
                "original_file_path": "models/marts/core/example_mart.sql",
                "name": "example_mart",
                "description": "A documented mart.",
                "columns": {"record_key": {"description": "Documented key."}},
            }
        },
        "sources": {
            source_id: {
                "package_name": "nyc_building_compliance",
                "source_name": "dob_raw",
                "name": "example_source",
                "description": "A documented source.",
                "columns": {"raw_payload": {"description": "Source payload."}},
            }
        },
        "exposures": {
            "exposure.nyc_building_compliance.example_dashboard": {
                "package_name": "nyc_building_compliance",
                "name": "example_dashboard",
                "description": "A documented consumer.",
                "owner": {"name": "Portfolio Owner"},
            }
        },
    }
    catalog = {
        "nodes": {
            model_id: {
                "columns": {"RECORD_KEY": {"name": "RECORD_KEY"}},
            }
        },
        "sources": {
            source_id: {
                "columns": {"RAW_PAYLOAD": {"name": "RAW_PAYLOAD"}},
            }
        },
    }
    return manifest, catalog


def test_documentation_audit_accepts_complete_published_assets() -> None:
    manifest, catalog = _artifacts()

    audit = audit_documentation(manifest, catalog)

    assert audit.errors == []
    assert audit.documented_published_columns == audit.published_columns == 1
    assert audit.documented_source_columns == audit.source_columns == 1


def test_documentation_audit_reports_undocumented_physical_column() -> None:
    manifest, catalog = _artifacts()
    manifest["nodes"]["model.nyc_building_compliance.example_mart"]["columns"] = {}

    audit = audit_documentation(manifest, catalog)

    assert any("undocumented physical columns: record_key" in error for error in audit.errors)


def test_documentation_audit_rejects_placeholder_exposure_metadata() -> None:
    manifest, catalog = _artifacts()
    exposure = next(iter(manifest["exposures"].values()))
    exposure["url"] = "https://example.invalid/replace-with-bi-url"

    audit = audit_documentation(manifest, catalog)

    assert any("placeholder metadata found" in error for error in audit.errors)


def test_documentation_audit_reports_stale_column_declaration() -> None:
    manifest, catalog = _artifacts()
    manifest_copy = deepcopy(manifest)
    model = manifest_copy["nodes"]["model.nyc_building_compliance.example_mart"]
    model["columns"]["removed_column"] = {"description": "No longer physical."}

    audit = audit_documentation(manifest_copy, catalog)

    assert any("documented columns absent from warehouse" in error for error in audit.errors)
