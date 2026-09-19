import hashlib
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .datasets import Dataset
from .socrata import SocrataClient


@dataclass(frozen=True)
class ExtractManifest:
    dataset_name: str
    dataset_id: str
    source_url: str
    extracted_at: str
    requested_limit: int
    page_size: int
    row_count: int
    page_count: int
    sha256: str
    output_file: str


def extract_to_jsonl(
    client: SocrataClient,
    dataset: Dataset,
    output_path: Path,
    *,
    limit: int,
    page_size: int,
) -> ExtractManifest:
    if limit < 1:
        raise ValueError("limit must be a positive integer")

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0
    page_count = 0
    digest = hashlib.sha256()

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_path.parent,
            prefix=f".{output_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
            for rows in client.pages(dataset, limit=limit, page_size=page_size):
                page_count += 1
                for row in rows:
                    line = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
                    text_line = f"{line}\n"
                    temporary_file.write(text_line)
                    digest.update(text_line.encode("utf-8"))
                    row_count += 1
        os.replace(temporary_path, output_path)
    except Exception:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()
        raise

    manifest = ExtractManifest(
        dataset_name=dataset.name,
        dataset_id=dataset.dataset_id,
        source_url=f"https://data.cityofnewyork.us/resource/{dataset.dataset_id}.json",
        extracted_at=datetime.now(UTC).isoformat(),
        requested_limit=limit,
        page_size=page_size,
        row_count=row_count,
        page_count=page_count,
        sha256=digest.hexdigest(),
        output_file=str(output_path),
    )
    manifest_path = output_path.with_suffix(".manifest.json")
    manifest_path.write_text(f"{json.dumps(asdict(manifest), indent=2)}\n", encoding="utf-8")
    return manifest
