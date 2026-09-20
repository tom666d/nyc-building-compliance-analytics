# Source profile

Profile date: 2026-09-19 (America/Chicago)

This profile records reproducible observations from the official NYC Open Data Socrata endpoints. Counts are point-in-time evidence and will change as the daily datasets refresh.

## Dataset overview

| Dataset | Socrata ID | Rows | Columns | Distinct BINs | Source update observed |
|---|---:|---:|---:|---:|---|
| DOB NOW: Build – Approved Permits | `rbx6-tga4` | 1,002,770 | 46 | 145,631 | 2026-09-19 13:41 CDT |
| DOB Complaints Received | `eabe-havv` | 3,133,744 | 15 | 525,218 | 2026-09-19 11:18 CDT |
| DOB Violations | `3h2n-5cm9` | 2,476,860 | 18 | 242,494 | 2026-09-19 12:38 CDT |

Combined source volume at profiling time: 6,613,374 rows.

## First warehouse sample

On 2026-09-20, the ingestion pipeline loaded a bounded 1,000-row sample from each official source into Snowflake. All three samples contained 1,000 distinct canonical source-row hashes.

The staging profile found two malformed legacy violation issue-date strings: `02230913` and `0306`. Automatic conversion interpreted the first as the year 223. The model now preserves the original source value, returns a null typed date, and exposes an `issue_date_parse_failed` flag rather than guessing a correction.

## API and schema observations

- Dataset metadata is available at `https://data.cityofnewyork.us/api/views/{dataset_id}`.
- Records are available at `https://data.cityofnewyork.us/resource/{dataset_id}.json`.
- Permit dates are declared as `calendar_date`; complaint and legacy violation dates are declared as text.
- Sample complaint dates use `MM/DD/YYYY`.
- Sample legacy violation dates use `YYYYMMDD`.
- All three datasets expose BIN, but the field name and neighboring address conventions vary.

## Key and duplicate profiling

### Complaints

- 3,133,744 rows and 3,133,738 distinct complaint numbers were observed.
- Six complaint numbers occurred twice.
- The inspected duplicate for complaint `2124643` contained two byte-equivalent API payloads.
- Phase 1 can therefore treat complaint number as the business identifier while removing exact duplicate payloads and monitoring uniqueness.

### Legacy violations

- All 2,476,860 values of `isn_dob_bis_viol` were distinct at profiling time.
- 2,473,646 rows had BIN; 3,214 rows (0.1298%) did not.
- Records without BIN must remain in the event fact but cannot safely enter building-level aggregates without another validated identity rule.

### Permits

The initial key hypothesis—job filing number, work permit, and sequence number—failed profiling.

- Some key combinations represented multiple tracking numbers and multiple work types.
- Example: one profiled work-permit sequence contained 12 rows: three tracking numbers multiplied by four work types.
- Adding tracking number and work type still left exact duplicate source payloads in some cases.
- Tracking number alone is not globally unique and can map to different job filings and issue dates.
- Some legitimate records use placeholder values such as `Permit is no` and `Permit is not yet issued`, so filtering those strings would remove real activity.

Conclusion: no source-provided field or currently tested combination is a validated permit natural key. The permit fact grain remains provisional. Exact duplicate payloads can be removed safely, but collapsing distinct rows requires a documented permit/work-type or permit-issuance model.

## Current status distributions

| Domain | Source value | Rows |
|---|---|---:|
| Complaint | `CLOSED` | 3,112,656 |
| Complaint | `ACTIVE` | 21,088 |
| Permit | `Signed-off` | 640,066 |
| Permit | `Permit Issued` | 362,704 |
| Legacy violation | `V-DOB VIOLATION - ACTIVE` | 552,346 |
| Legacy violation | `V*-DOB VIOLATION - Resolved` | 673,667 |
| Legacy violation | `V*-DOB VIOLATION - DISMISSED` | 1,170,075 |

The violation source contains additional active and dismissed category strings. Models must map explicit source categories rather than infer open status only from a missing disposition date.

## Modeling consequences

1. Do not release the current permit fact until its grain is revised and tested.
2. Deduplicate exact raw payloads separately from business-key version handling.
3. Parse dates with source-specific rules and test parsing failures.
4. Use explicit source status mappings; do not assume one universal `OPEN`/`CLOSED` vocabulary.
5. Publish unmatched-BIN coverage so building-level totals can be reconciled to event totals.
6. Retain source dataset ID, ingestion timestamp, load identifier, and row hash for traceability.

## Reproducible query examples

Count rows:

```text
GET https://data.cityofnewyork.us/resource/eabe-havv.json?$select=count(*)
```

Profile complaint key coverage:

```text
GET https://data.cityofnewyork.us/resource/eabe-havv.json
    ?$select=count(*) as total_rows,
             count(distinct complaint_number) as distinct_keys
```

Find duplicate permit key hypotheses:

```text
GET https://data.cityofnewyork.us/resource/rbx6-tga4.json
    ?$select=job_filing_number,work_permit,sequence_number,count(*) as row_count
    &$group=job_filing_number,work_permit,sequence_number
    &$having=count(*) > 1
    &$order=row_count desc
```

These examples use Socrata Query Language and must be URL-encoded by a client before transmission.
