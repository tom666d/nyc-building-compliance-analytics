from collections.abc import Iterator
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .datasets import Dataset


class SocrataClient:
    def __init__(
        self,
        app_token: str | None = None,
        timeout_seconds: int = 60,
        session: requests.Session | None = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.session = session or self._build_session()
        self.session.headers.update({"User-Agent": "nyc-building-compliance/0.1.0"})
        if app_token:
            self.session.headers.update({"X-App-Token": app_token})

    @staticmethod
    def _build_session() -> requests.Session:
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry))
        return session

    def pages(
        self, dataset: Dataset, *, limit: int | None = None, page_size: int = 10_000
    ) -> Iterator[list[dict[str, Any]]]:
        if limit is not None and limit < 1:
            raise ValueError("limit must be a positive integer or None")
        if not 1 <= page_size <= 50_000:
            raise ValueError("page_size must be between 1 and 50,000")

        offset = 0
        remaining = limit
        url = f"https://data.cityofnewyork.us/resource/{dataset.dataset_id}.json"

        while remaining is None or remaining > 0:
            batch_size = min(page_size, remaining) if remaining is not None else page_size
            response = self.session.get(
                url,
                params={"$limit": batch_size, "$offset": offset, "$order": dataset.order_by},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            rows = response.json()
            if not isinstance(rows, list):
                raise TypeError(f"expected a JSON array from dataset {dataset.dataset_id}")
            if not rows:
                return
            yield rows
            offset += len(rows)
            if remaining is not None:
                remaining -= len(rows)
            if len(rows) < batch_size:
                return
