import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any


def canonical_json(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def row_hash(row: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(row).encode()).hexdigest()


def load_rows(connection, table: str, dataset_id: str, rows: list[dict[str, Any]]) -> int:
    """Append immutable raw payloads; downstream staging retains the latest row hash."""
    load_id = str(uuid.uuid4())
    ingested_at = datetime.now(UTC)
    values = [
        (canonical_json(row), dataset_id, row_hash(row), load_id, ingested_at) for row in rows
    ]
    sql = f"""
        insert into {table}
          (raw_payload, source_dataset_id, source_row_hash, load_id, ingested_at)
        select parse_json(column1), column2, column3, column4, column5
        from values (%s, %s, %s, %s, %s)
    """
    with connection.cursor() as cursor:
        cursor.executemany(sql, values)
    return len(values)
