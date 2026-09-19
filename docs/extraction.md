# Local source extraction

The local extraction command downloads a bounded real-data sample from an official NYC Open Data endpoint without requiring a Snowflake account. It is designed for source inspection, onboarding, and deterministic pipeline testing—not yet for the full production load.

## Command

```bash
nyc-dob-extract complaints --limit 100 --page-size 25
```

Available dataset names:

- `permits` → `rbx6-tga4`
- `complaints` → `eabe-havv`
- `violations` → `3h2n-5cm9`

The default output is `work/samples/{dataset}.jsonl`. A different path can be selected with `--output`. The optional `NYC_OPEN_DATA_APP_TOKEN` environment variable is sent as `X-App-Token`; credentials are never embedded in code.

## Output contract

Each run writes two local files:

1. `{dataset}.jsonl`: one source JSON object per line;
2. `{dataset}.manifest.json`: extraction metadata used for audit and validation.

Example manifest:

```json
{
  "dataset_name": "complaints",
  "dataset_id": "eabe-havv",
  "source_url": "https://data.cityofnewyork.us/resource/eabe-havv.json",
  "extracted_at": "2026-09-19T20:45:35.455442+00:00",
  "requested_limit": 25,
  "page_size": 1000,
  "row_count": 25,
  "page_count": 1,
  "sha256": "31bbf23c2328a49c6cfed84fc2b0fa74983e42d43d978b24f481e9deb3e37bdb",
  "output_file": "/local/path/work/samples/complaints.jsonl"
}
```

The files are intentionally ignored by Git because they are source snapshots that change over time. The code, tests, and output contract are versioned instead.

## Reliability behavior

- Every request has an explicit timeout.
- HTTP 429 and transient server errors are retried up to three times with backoff.
- A named User-Agent identifies the portfolio client.
- Socrata paging uses `$limit`, `$offset`, and the platform-recommended `:id` order.
- Page size is constrained to 1–50,000 for the endpoint version used here.
- A non-array API response fails explicitly instead of being treated as valid rows.
- Data is written to a temporary file and atomically renamed only after extraction succeeds.
- The manifest records row/page counts and a SHA-256 file digest.

## Verified Step 4 run

On 2026-09-19, the command downloaded 25 rows from each configured source. All three files passed JSON parsing, line-count, and SHA-256 verification. A separate five-row complaint run with a two-row page size produced three pages, confirming multi-page behavior.

Automated tests cover:

- dataset ID uniqueness;
- deterministic raw-row hashing;
- limit and offset behavior across pages;
- stable `:id` ordering;
- invalid page-size rejection;
- JSON Lines output and manifest creation.

## Current limitations

- Offset pagination can observe a moving dataset during a long full extract, even with stable ordering.
- The command performs bounded extraction, not date-watermarked incremental loading.
- Raw values are intentionally not typed or normalized at extraction time.
- Source schema validation and drift alerts are not implemented yet.
- Full-load checkpointing and restart-from-page behavior are not implemented yet.

These limitations keep Step 4 small and observable. The production ingestion strategy will be chosen after source mutation and incremental fields are profiled.
