select
  'permit_records' as domain,
  permit_key::varchar as record_key,
  permit_status as source_status,
  source_dataset_id,
  ingested_at
from {{ ref('fct_permit_records') }}
where is_status_unmapped

union all

select
  'complaints' as domain,
  complaint_key::varchar as record_key,
  complaint_status as source_status,
  source_dataset_id,
  ingested_at
from {{ ref('fct_complaints') }}
where is_status_unmapped

union all

select
  'violations' as domain,
  violation_key::varchar as record_key,
  violation_category as source_status,
  source_dataset_id,
  ingested_at
from {{ ref('fct_violations') }}
where is_status_unmapped
