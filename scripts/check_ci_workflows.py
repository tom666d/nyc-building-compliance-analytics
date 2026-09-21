"""Enforce security and coverage contracts for tracked GitHub Actions workflows."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ACTION_SHA_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_workflow(path: Path) -> dict[str, Any]:
    content = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
    if not isinstance(content, dict):
        raise TypeError(f"{path.name} is not a YAML mapping")
    return content


def _steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for job in workflow.get("jobs", {}).values():
        result.extend(job.get("steps", []))
    return result


def _run_commands(workflow: dict[str, Any]) -> str:
    return "\n".join(str(step.get("run", "")) for step in _steps(workflow))


def _audit_common(path: Path, workflow: dict[str, Any]) -> list[str]:
    errors = []
    permissions = workflow.get("permissions", {})
    if permissions != {"contents": "read"}:
        errors.append(f"{path.name}: top-level permissions must be contents: read only")

    for step in _steps(workflow):
        action = step.get("uses")
        if action and not str(action).startswith("./") and not ACTION_SHA_PATTERN.fullmatch(action):
            errors.append(f"{path.name}: action is not pinned to a full commit SHA: {action}")

    for job_name, job in workflow.get("jobs", {}).items():
        timeout = job.get("timeout-minutes")
        if timeout is None or int(timeout) > 30:
            errors.append(f"{path.name}: {job_name} must have a timeout of at most 30 minutes")

    if "pull_request_target" in workflow.get("on", {}):
        errors.append(f"{path.name}: pull_request_target is prohibited")
    return errors


def audit_workflows(workflow_directory: Path) -> list[str]:
    ci_path = workflow_directory / "ci.yml"
    integration_path = workflow_directory / "snowflake-integration.yml"
    errors = []

    for path in (ci_path, integration_path):
        if not path.exists():
            errors.append(f"Missing workflow: {path.name}")
    if errors:
        return errors

    ci = _load_workflow(ci_path)
    integration = _load_workflow(integration_path)
    errors.extend(_audit_common(ci_path, ci))
    errors.extend(_audit_common(integration_path, integration))

    ci_triggers = set(ci.get("on", {}))
    if ci_triggers != {"pull_request", "push", "workflow_dispatch"}:
        errors.append("ci.yml: expected pull_request, push, and workflow_dispatch triggers")
    ci_text = ci_path.read_text()
    if "secrets." in ci_text:
        errors.append("ci.yml: static validation must not read GitHub secrets")
    if ci.get("concurrency", {}).get("cancel-in-progress") != "true":
        errors.append("ci.yml: stale validation runs must be cancellable")

    ci_commands = _run_commands(ci)
    required_ci_commands = {
        "make ci-workflow-check",
        "make lint",
        "make test",
        ".venv/bin/pip check",
        "make dbt-deps",
        "make dbt-parse",
        "make airflow-check",
        "make dashboard-install",
        "make dashboard-check",
        ".airflow-venv/bin/pip check",
    }
    for command in sorted(required_ci_commands):
        if command not in ci_commands:
            errors.append(f"ci.yml: missing required validation command: {command}")

    integration_triggers = set(integration.get("on", {}))
    if integration_triggers != {"workflow_dispatch"}:
        errors.append("snowflake-integration.yml: live warehouse access must be manual only")
    integration_text = integration_path.read_text()
    if "secrets.SNOWFLAKE_PASSWORD" in integration_text:
        errors.append("snowflake-integration.yml: password authentication is prohibited")
    if "secrets.SNOWFLAKE_PRIVATE_KEY_B64" not in integration_text:
        errors.append("snowflake-integration.yml: key-pair authentication is required")

    integration_jobs = integration.get("jobs", {})
    for job_name, job in integration_jobs.items():
        if job.get("environment") != "snowflake-integration":
            errors.append(f"snowflake-integration.yml: {job_name} needs the protected environment")
        if "inputs.confirm_cost" not in str(job.get("if", "")):
            errors.append(f"snowflake-integration.yml: {job_name} needs explicit cost confirmation")
        for value in job.get("env", {}).values():
            if "runner." in str(value):
                errors.append(
                    "snowflake-integration.yml: runner context is unavailable in job-level env"
                )

    integration_commands = _run_commands(integration)
    for command in ("make dbt-build", "make dbt-docs-check"):
        if command not in integration_commands:
            errors.append(f"snowflake-integration.yml: missing required command: {command}")
    for required_fragment in ("$RUNNER_TEMP", "$GITHUB_ENV"):
        if required_fragment not in integration_commands:
            errors.append(
                "snowflake-integration.yml: temporary key path must be exported "
                f"through GITHUB_ENV using {required_fragment}"
            )

    return errors


def main() -> int:
    workflow_directory = PROJECT_ROOT / ".github" / "workflows"
    errors = audit_workflows(workflow_directory)
    if errors:
        print("GitHub Actions workflow contract failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("GitHub Actions workflow contract passed.")
    print("  static CI: pull request, main push, and manual triggers")
    print("  live Snowflake integration: manual and environment-protected")
    print("  token permissions: repository contents read-only")
    print("  external actions: pinned to full commit SHAs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
