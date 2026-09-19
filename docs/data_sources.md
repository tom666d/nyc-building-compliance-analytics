# Official data sources

All Phase 1 inputs are NYC Open Data datasets attributed to the NYC Department of Buildings and refreshed daily. The stable Socrata dataset identifier is treated as the source contract; page titles and schemas can still change, so ingestion stores a run timestamp and raw JSON.

| Domain | Official dataset | Socrata ID | Approx. grain | Phase 1 use |
|---|---|---:|---|---|
| Permit | [DOB NOW: Build – Approved Permits](https://data.cityofnewyork.us/d/rbx6-tga4) | `rbx6-tga4` | issued/approved work permit sequence | included |
| Complaint | [DOB Complaints Received](https://data.cityofnewyork.us/d/eabe-havv) | `eabe-havv` | complaint number | included |
| Legacy violation | [DOB Violations](https://data.cityofnewyork.us/d/3h2n-5cm9) | `3h2n-5cm9` | BIS violation record | included |
| Newer violation | [DOB Safety Violations](https://data.cityofnewyork.us/d/855j-jady) | `855j-jady` | DOB NOW safety violation | deferred |

API base: `https://data.cityofnewyork.us/resource/{dataset_id}.json`

## Why the newer violation dataset is deferred

NYC states that some records overlap between legacy DOB Violations and newer DOB Safety Violations. Unioning them would inflate counts. Phase 2 will profile candidate crosswalks using BIN, violation number/type, issue date, device number, and source system, then publish match-rate evidence before a combined fact is released.

## Known quality risks

- BIN can be blank, malformed, or represent a source-system limitation.
- Status strings and business meanings may change without a versioned API.
- Open Data is a daily analytical extract, not a transactional feed.
- Complaints can originate from 311 or be entered by DOB staff.
- “No disposition date” is used as the initial legacy violation open rule and requires domain validation.
- Daily source extracts can update prior rows; ingestion therefore supports replay windows and idempotent merge keys.

## Extraction policy

- Use explicit field selection rather than `select *` at the modeled layer.
- Page deterministically using the dataset's stable natural key.
- Apply server-side date filters for incremental runs.
- Store `_ingested_at`, `_source_dataset_id`, `_source_row_hash`, and `_load_id` with every raw record.
- Never silently drop records missing BIN; surface them in quality reporting.

## Profiling evidence

The point-in-time live-source profile, including row counts, key tests, status distributions, and the failed permit-grain hypothesis, is documented in [source_profile.md](source_profile.md). The evidence shows that the permit grain is provisional and that the staging scaffold must be revised before its first warehouse build.
