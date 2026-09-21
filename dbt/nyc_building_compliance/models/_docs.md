{% docs __overview__ %}

# NYC Building Compliance & Permit Analytics Platform

This dbt project integrates three official NYC Department of Buildings datasets into
tested, building-level decision products. Use the lineage graph to trace published
metrics from their business intelligence exposures through marts and staging models to
the original NYC Open Data sources.

The published layer contains:

- a conformed building dimension;
- permit, complaint, and violation event facts;
- a daily building compliance snapshot for business intelligence;
- a quality scorecard and record-level exception views.

The project uses a bounded real-data sample for reproducible portfolio validation. Source
limitations and provisional definitions remain visible in the model descriptions and
architecture decision records rather than being hidden in dashboard logic.

{% enddocs %}

{% docs building_key %}

Deterministic warehouse surrogate key generated from the validated seven-digit NYC
Building Identification Number. This is the conformed join key for building-level
analytics; it is not an identifier supplied by NYC Open Data.

{% enddocs %}

{% docs bin %}

Validated seven-digit NYC Building Identification Number supplied by the Department of
Buildings. Invalid or missing values become null rather than being silently repaired.

{% enddocs %}

{% docs source_dataset_id %}

NYC Open Data dataset identifier captured during ingestion, allowing a published record
to be traced to its official source dataset.

{% enddocs %}

{% docs source_row_hash %}

SHA-256 fingerprint of the canonical raw source payload. It supports exact-payload
deduplication and traceability without pretending to be a business identifier.

{% enddocs %}

{% docs source_load_id %}

Identifier of the ingestion execution that most recently supplied the retained source
record.

{% enddocs %}

{% docs ingested_at %}

Timestamp when the ingestion process wrote the source record to Snowflake. It represents
pipeline arrival time, not the real-world event time.

{% enddocs %}

{% docs is_status_unmapped %}

Boolean governance flag that is true when the current source status is not covered by the
explicit analytical mapping. Unmapped values are retained for investigation and block
publication through a data test.

{% enddocs %}

{% docs audit_domain %}

Event domain being measured: `permit_records`, `complaints`, or `violations`.

{% enddocs %}

{% docs audit_record_key %}

Source-aligned record identifier used to locate the exact fact row that triggered a
quality exception. Interpret it together with `domain` because key formats differ across
sources.

{% enddocs %}
