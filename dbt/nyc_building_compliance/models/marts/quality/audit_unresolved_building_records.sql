select
  'permit_records' as domain,
  permit_key::varchar as record_key,
  bin as source_bin,
  permit_status_group as event_status_group,
  iff(bin is null, 'MISSING_OR_INVALID_BIN', 'UNMATCHED_VALID_BIN') as quality_issue,
  source_dataset_id,
  ingested_at
from {{ ref('fct_permit_records') }}
where building_key is null

union all

select
  'complaints' as domain,
  complaint_key::varchar as record_key,
  bin as source_bin,
  complaint_status_group as event_status_group,
  iff(bin is null, 'MISSING_OR_INVALID_BIN', 'UNMATCHED_VALID_BIN') as quality_issue,
  source_dataset_id,
  ingested_at
from {{ ref('fct_complaints') }}
where building_key is null

union all

select
  'violations' as domain,
  violation_key::varchar as record_key,
  bin as source_bin,
  violation_status_group as event_status_group,
  iff(bin is null, 'MISSING_OR_INVALID_BIN', 'UNMATCHED_VALID_BIN') as quality_issue,
  source_dataset_id,
  ingested_at
from {{ ref('fct_violations') }}
where building_key is null
