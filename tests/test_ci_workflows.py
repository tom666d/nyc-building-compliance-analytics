import importlib.util
import sys
from pathlib import Path
from shutil import copytree

WORKFLOW_DIRECTORY = Path(__file__).parents[1] / ".github" / "workflows"
SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "check_ci_workflows.py"
SPEC = importlib.util.spec_from_file_location("check_ci_workflows", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
CI_WORKFLOW_MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CI_WORKFLOW_MODULE
SPEC.loader.exec_module(CI_WORKFLOW_MODULE)
audit_workflows = CI_WORKFLOW_MODULE.audit_workflows


def _workflow_copy(tmp_path: Path) -> Path:
    destination = tmp_path / "workflows"
    copytree(WORKFLOW_DIRECTORY, destination)
    return destination


def test_tracked_workflows_satisfy_ci_contract():
    assert audit_workflows(WORKFLOW_DIRECTORY) == []


def test_ci_contract_rejects_mutable_action_tags(tmp_path):
    workflows = _workflow_copy(tmp_path)
    ci_path = workflows / "ci.yml"
    content = ci_path.read_text().replace(
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/checkout@v7",
    )
    ci_path.write_text(content)

    errors = audit_workflows(workflows)

    assert any("not pinned to a full commit SHA" in error for error in errors)


def test_ci_contract_rejects_secrets_in_static_validation(tmp_path):
    workflows = _workflow_copy(tmp_path)
    ci_path = workflows / "ci.yml"
    content = ci_path.read_text().replace(
        '  PIP_DISABLE_PIP_VERSION_CHECK: "1"',
        '  PIP_DISABLE_PIP_VERSION_CHECK: "1"\n  UNSAFE: ${{ secrets.UNSAFE }}',
    )
    ci_path.write_text(content)

    errors = audit_workflows(workflows)

    assert any("static validation must not read GitHub secrets" in error for error in errors)


def test_ci_contract_rejects_automatic_snowflake_trigger(tmp_path):
    workflows = _workflow_copy(tmp_path)
    integration_path = workflows / "snowflake-integration.yml"
    content = integration_path.read_text().replace(
        "on:\n  workflow_dispatch:",
        "on:\n  pull_request:\n  workflow_dispatch:",
    )
    integration_path.write_text(content)

    errors = audit_workflows(workflows)

    assert any("live warehouse access must be manual only" in error for error in errors)


def test_ci_contract_rejects_runner_context_in_job_environment(tmp_path):
    workflows = _workflow_copy(tmp_path)
    integration_path = workflows / "snowflake-integration.yml"
    content = integration_path.read_text().replace(
        "      SNOWFLAKE_SCHEMA: DEV",
        "      SNOWFLAKE_SCHEMA: DEV\n"
        "      SNOWFLAKE_PRIVATE_KEY_PATH: ${{ runner.temp }}/snowflake_key.p8",
    )
    integration_path.write_text(content)

    errors = audit_workflows(workflows)

    assert any("runner context is unavailable in job-level env" in error for error in errors)
