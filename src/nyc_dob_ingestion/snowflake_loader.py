import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Any

MERGE_BATCH_SIZE = 250


def canonical_json(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def row_hash(row: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(row).encode()).hexdigest()


def load_rows(
    connection,
    table: str,
    dataset_id: str,
    rows: list[dict[str, Any]],
    *,
    load_id: str | None = None,
) -> int:
    """Insert source payloads idempotently for one stable load identifier."""
    resolved_load_id = load_id or str(uuid.uuid4())
    ingested_at = datetime.now(UTC)
    unique_rows = {row_hash(row): row for row in rows}
    values = [
        (
            canonical_json(row),
            dataset_id,
            source_row_hash,
            resolved_load_id,
            ingested_at,
        )
        for source_row_hash, row in unique_rows.items()
    ]
    if not values:
        return 0

    affected_rows = 0
    with connection.cursor() as cursor:
        for offset in range(0, len(values), MERGE_BATCH_SIZE):
            batch = values[offset : offset + MERGE_BATCH_SIZE]
            placeholders = ",\n".join(["(%s, %s, %s, %s, %s)"] * len(batch))
            sql = f"""
                merge into {table} as target
                using (
                  select
                    parse_json(column1::varchar) as raw_payload,
                    column2::varchar as source_dataset_id,
                    column3::varchar as source_row_hash,
                    column4::varchar as load_id,
                    column5::timestamp_tz as ingested_at
                  from values
                    {placeholders}
                ) as incoming
                  on target.source_row_hash = incoming.source_row_hash
                 and target.load_id = incoming.load_id
                when not matched then insert
                  (raw_payload, source_dataset_id, source_row_hash, load_id, ingested_at)
                values
                  (incoming.raw_payload, incoming.source_dataset_id,
                   incoming.source_row_hash, incoming.load_id, incoming.ingested_at)
            """
            parameters = tuple(item for row in batch for item in row)
            cursor.execute(sql, parameters)
            affected_rows += cursor.rowcount if cursor.rowcount >= 0 else len(batch)
    return affected_rows
