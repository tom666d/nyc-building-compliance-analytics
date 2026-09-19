from collections.abc import Iterator
from typing import Any

import requests

from .datasets import Dataset


class SocrataClient:
    def __init__(self, app_token: str | None = None, timeout_seconds: int = 60):
        self.app_token = app_token
        self.timeout_seconds = timeout_seconds

    def pages(
        self, dataset: Dataset, *, limit: int | None = None, page_size: int = 10_000
    ) -> Iterator[list[dict[str, Any]]]:
        offset = 0
        remaining = limit
        headers = {"X-App-Token": self.app_token} if self.app_token else {}
        url = f"https://data.cityofnewyork.us/resource/{dataset.dataset_id}.json"

        while remaining is None or remaining > 0:
            batch_size = min(page_size, remaining) if remaining is not None else page_size
            response = requests.get(
                url,
                headers=headers,
                params={"$limit": batch_size, "$offset": offset, "$order": dataset.order_by},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            rows = response.json()
            if not rows:
                return
            yield rows
            offset += len(rows)
            if remaining is not None:
                remaining -= len(rows)
            if len(rows) < batch_size:
                return
