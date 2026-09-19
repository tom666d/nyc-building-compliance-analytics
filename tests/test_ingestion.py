from nyc_dob_ingestion.datasets import DATASETS
from nyc_dob_ingestion.snowflake_loader import canonical_json, row_hash


def test_dataset_ids_are_unique():
    assert len({item.dataset_id for item in DATASETS.values()}) == len(DATASETS)


def test_row_hash_is_stable_across_key_order():
    left = {"bin": "1000001", "status": "OPEN"}
    right = {"status": "OPEN", "bin": "1000001"}
    assert canonical_json(left) == canonical_json(right)
    assert row_hash(left) == row_hash(right)


def test_changed_payload_changes_hash():
    assert row_hash({"status": "OPEN"}) != row_hash({"status": "CLOSED"})
