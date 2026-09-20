import json

import pytest

from nyc_dob_ingestion.datasets import DATASETS
from nyc_dob_ingestion.extract import extract_to_jsonl
from nyc_dob_ingestion.snowflake import (
    SnowflakeConfigurationError,
    connection_parameters_from_env,
)
from nyc_dob_ingestion.snowflake_loader import canonical_json, row_hash
from nyc_dob_ingestion.socrata import SocrataClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payloads):
        self.payloads = iter(payloads)
        self.headers = {}
        self.calls = []

    def get(self, url, *, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(next(self.payloads))


def test_dataset_ids_are_unique():
    assert len({item.dataset_id for item in DATASETS.values()}) == len(DATASETS)


def test_row_hash_is_stable_across_key_order():
    left = {"bin": "1000001", "status": "OPEN"}
    right = {"status": "OPEN", "bin": "1000001"}
    assert canonical_json(left) == canonical_json(right)
    assert row_hash(left) == row_hash(right)


def test_changed_payload_changes_hash():
    assert row_hash({"status": "OPEN"}) != row_hash({"status": "CLOSED"})


def test_socrata_pages_respect_limit_and_use_stable_order():
    session = FakeSession([[{"id": 1}, {"id": 2}], [{"id": 3}]])
    client = SocrataClient(session=session, timeout_seconds=12)

    pages = list(client.pages(DATASETS["complaints"], limit=3, page_size=2))

    assert pages == [[{"id": 1}, {"id": 2}], [{"id": 3}]]
    assert session.calls[0]["params"] == {"$limit": 2, "$offset": 0, "$order": ":id"}
    assert session.calls[1]["params"] == {"$limit": 1, "$offset": 2, "$order": ":id"}
    assert session.calls[0]["timeout"] == 12


@pytest.mark.parametrize("page_size", [0, 50_001])
def test_socrata_pages_reject_invalid_page_size(page_size):
    client = SocrataClient(session=FakeSession([]))

    with pytest.raises(ValueError, match="page_size"):
        list(client.pages(DATASETS["complaints"], limit=1, page_size=page_size))


def test_extract_writes_json_lines_and_manifest(tmp_path):
    session = FakeSession([[{"status": "ACTIVE", "bin": "1000001"}]])
    client = SocrataClient(session=session)
    output = tmp_path / "complaints.jsonl"

    manifest = extract_to_jsonl(
        client,
        DATASETS["complaints"],
        output,
        limit=1,
        page_size=1,
    )

    assert json.loads(output.read_text()) == {"bin": "1000001", "status": "ACTIVE"}
    assert manifest.row_count == 1
    assert manifest.page_count == 1
    assert len(manifest.sha256) == 64
    written_manifest = json.loads(output.with_suffix(".manifest.json").read_text())
    assert written_manifest["dataset_id"] == "eabe-havv"


def test_snowflake_connection_uses_least_privilege_workload_defaults():
    environment = {
        "SNOWFLAKE_ACCOUNT": "example-account",
        "SNOWFLAKE_USER": "example-user",
        "SNOWFLAKE_PASSWORD": "not-a-real-secret",
        "SNOWFLAKE_SCHEMA": "CUSTOM_DBT_SCHEMA",
    }

    loader = connection_parameters_from_env("loader", environment)
    transformer = connection_parameters_from_env("transformer", environment)
    reader = connection_parameters_from_env("reader", environment)

    assert (loader["role"], loader["schema"]) == ("NYC_DOB_LOADER", "RAW")
    assert (transformer["role"], transformer["schema"]) == (
        "NYC_DOB_TRANSFORMER",
        "CUSTOM_DBT_SCHEMA",
    )
    assert (reader["role"], reader["schema"]) == ("NYC_DOB_READER", "DEV_MARTS")


def test_snowflake_connection_allows_explicit_role_override():
    environment = {
        "SNOWFLAKE_ACCOUNT": "example-account",
        "SNOWFLAKE_USER": "example-user",
        "SNOWFLAKE_PASSWORD": "not-a-real-secret",
        "SNOWFLAKE_INGEST_ROLE": "CUSTOM_LOADER",
    }

    parameters = connection_parameters_from_env("loader", environment)

    assert parameters["role"] == "CUSTOM_LOADER"


def test_snowflake_connection_supports_encrypted_private_key():
    environment = {
        "SNOWFLAKE_ACCOUNT": "example-account",
        "SNOWFLAKE_USER": "example-service-user",
        "SNOWFLAKE_PRIVATE_KEY_PATH": "/local/secrets/snowflake_key.p8",
        "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "not-a-real-passphrase",
    }

    parameters = connection_parameters_from_env("loader", environment)

    assert parameters["authenticator"] == "SNOWFLAKE_JWT"
    assert parameters["private_key_file"] == environment["SNOWFLAKE_PRIVATE_KEY_PATH"]
    assert parameters["private_key_file_pwd"] == environment[
        "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE"
    ]
    assert "password" not in parameters


def test_snowflake_connection_rejects_multiple_authentication_methods():
    environment = {
        "SNOWFLAKE_ACCOUNT": "example-account",
        "SNOWFLAKE_USER": "example-service-user",
        "SNOWFLAKE_PASSWORD": "not-a-real-secret",
        "SNOWFLAKE_PRIVATE_KEY_PATH": "/local/secrets/snowflake_key.p8",
        "SNOWFLAKE_PRIVATE_KEY_PASSPHRASE": "not-a-real-passphrase",
    }

    with pytest.raises(SnowflakeConfigurationError, match="one authentication method"):
        connection_parameters_from_env("loader", environment)


def test_snowflake_connection_reports_variable_names_but_not_secret_values():
    with pytest.raises(SnowflakeConfigurationError) as error:
        connection_parameters_from_env(
            "loader",
            {"SNOWFLAKE_ACCOUNT": "", "SNOWFLAKE_USER": ""},
        )

    message = str(error.value)
    assert "SNOWFLAKE_ACCOUNT" in message
    assert "SNOWFLAKE_USER" in message


def test_snowflake_connection_requires_an_authentication_method():
    with pytest.raises(SnowflakeConfigurationError) as error:
        connection_parameters_from_env(
            "loader",
            {"SNOWFLAKE_ACCOUNT": "example-account", "SNOWFLAKE_USER": "example-user"},
        )

    message = str(error.value)
    assert "SNOWFLAKE_PRIVATE_KEY_PATH" in message
    assert "SNOWFLAKE_PASSWORD" in message
