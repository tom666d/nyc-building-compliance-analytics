"""Fail when published dbt assets are missing discoverable documentation."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_TARGET = Path("dbt/nyc_building_compliance/target")
PROJECT_PACKAGE = "nyc_building_compliance"
PUBLISHED_MODEL_PATH_PREFIX = "models/marts/"
PLACEHOLDER_MARKERS = (
    "example.invalid",
    "example.com",
    "placeholder",
    "replace-me",
    "replace_with",
    "replace-with",
)


@dataclass
class DocumentationAudit:
    published_models: int = 0
    published_columns: int = 0
    documented_published_columns: int = 0
    sources: int = 0
    source_columns: int = 0
    documented_source_columns: int = 0
    exposures: int = 0
    errors: list[str] = field(default_factory=list)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run 'make dbt-docs' after building the dbt project."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _catalog_column_names(resource: dict[str, Any]) -> set[str]:
    return {
        str(column.get("name", key)).lower()
        for key, column in resource.get("columns", {}).items()
    }


def _manifest_columns(resource: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {name.lower(): value for name, value in resource.get("columns", {}).items()}


def _check_columns(
    *,
    resource_label: str,
    manifest_resource: dict[str, Any],
    catalog_resource: dict[str, Any] | None,
    audit: DocumentationAudit,
    is_source: bool,
) -> None:
    if catalog_resource is None:
        audit.errors.append(f"{resource_label}: missing from catalog.json")
        return

    physical_columns = _catalog_column_names(catalog_resource)
    declared_columns = _manifest_columns(manifest_resource)
    undocumented: list[str] = []

    for column_name in sorted(physical_columns):
        column = declared_columns.get(column_name)
        if column is None or not _has_text(column.get("description")):
            undocumented.append(column_name)

    stale_declarations = sorted(set(declared_columns) - physical_columns)
    if undocumented:
        audit.errors.append(
            f"{resource_label}: undocumented physical columns: {', '.join(undocumented)}"
        )
    if stale_declarations:
        audit.errors.append(
            f"{resource_label}: documented columns absent from warehouse: "
            f"{', '.join(stale_declarations)}"
        )

    if is_source:
        audit.source_columns += len(physical_columns)
        audit.documented_source_columns += len(physical_columns) - len(undocumented)
    else:
        audit.published_columns += len(physical_columns)
        audit.documented_published_columns += len(physical_columns) - len(undocumented)


def audit_documentation(
    manifest: dict[str, Any], catalog: dict[str, Any]
) -> DocumentationAudit:
    audit = DocumentationAudit()

    for unique_id, node in manifest.get("nodes", {}).items():
        is_published_model = (
            node.get("resource_type") == "model"
            and node.get("package_name") == PROJECT_PACKAGE
            and str(node.get("original_file_path", "")).startswith(
                PUBLISHED_MODEL_PATH_PREFIX
            )
        )
        if not is_published_model:
            continue

        audit.published_models += 1
        model_name = str(node.get("name", unique_id))
        if not _has_text(node.get("description")):
            audit.errors.append(f"model {model_name}: missing model description")
        _check_columns(
            resource_label=f"model {model_name}",
            manifest_resource=node,
            catalog_resource=catalog.get("nodes", {}).get(unique_id),
            audit=audit,
            is_source=False,
        )

    for unique_id, source in manifest.get("sources", {}).items():
        if source.get("package_name") != PROJECT_PACKAGE:
            continue

        audit.sources += 1
        source_name = f"{source.get('source_name')}.{source.get('name')}"
        if not _has_text(source.get("description")):
            audit.errors.append(f"source {source_name}: missing source-table description")
        _check_columns(
            resource_label=f"source {source_name}",
            manifest_resource=source,
            catalog_resource=catalog.get("sources", {}).get(unique_id),
            audit=audit,
            is_source=True,
        )

    for unique_id, exposure in manifest.get("exposures", {}).items():
        if exposure.get("package_name") != PROJECT_PACKAGE:
            continue

        audit.exposures += 1
        exposure_name = str(exposure.get("name", unique_id))
        if not _has_text(exposure.get("description")):
            audit.errors.append(f"exposure {exposure_name}: missing description")
        if not _has_text(exposure.get("owner", {}).get("name")):
            audit.errors.append(f"exposure {exposure_name}: missing owner name")

        serialized = json.dumps(exposure, sort_keys=True).lower()
        matched_markers = [marker for marker in PLACEHOLDER_MARKERS if marker in serialized]
        if matched_markers:
            audit.errors.append(
                f"exposure {exposure_name}: placeholder metadata found: "
                f"{', '.join(matched_markers)}"
            )

    if audit.published_models == 0:
        audit.errors.append("No published mart models were found in manifest.json")
    if audit.sources == 0:
        audit.errors.append("No project sources were found in manifest.json")
    if audit.exposures == 0:
        audit.errors.append("No project exposures were found in manifest.json")

    return audit


def _print_summary(audit: DocumentationAudit) -> None:
    print("dbt documentation coverage")
    print(f"  published models: {audit.published_models}")
    print(
        "  published columns: "
        f"{audit.documented_published_columns}/{audit.published_columns} documented"
    )
    print(f"  sources: {audit.sources}")
    print(
        f"  source columns: {audit.documented_source_columns}/{audit.source_columns} documented"
    )
    print(f"  exposures: {audit.exposures}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"Directory containing manifest.json and catalog.json (default: {DEFAULT_TARGET})",
    )
    args = parser.parse_args()

    try:
        manifest = _load_json(args.target_dir / "manifest.json")
        catalog = _load_json(args.target_dir / "catalog.json")
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}")
        return 1

    audit = audit_documentation(manifest, catalog)
    _print_summary(audit)
    if audit.errors:
        print("Documentation contract failed:")
        for error in audit.errors:
            print(f"  - {error}")
        return 1

    print("Documentation contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
