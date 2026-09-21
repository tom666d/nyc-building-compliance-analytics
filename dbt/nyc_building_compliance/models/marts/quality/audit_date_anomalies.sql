select
  'permit_records' as domain,
  permit_key::varchar as record_key,
  'ISSUED_BEFORE_APPROVED' as quality_issue,
  concat_ws(
    ' | ',
    'approved=' || coalesce(to_varchar(approved_date), 'NULL'),
    'issued=' || coalesce(to_varchar(issued_date), 'NULL')
  ) as source_value,
  source_dataset_id,
  ingested_at
from {{ ref('fct_permit_records') }}
where coalesce(approval_to_issue_date_anomaly, false)

union all

select
  'complaints' as domain,
  complaint_key::varchar as record_key,
  'DISPOSITION_BEFORE_ENTERED' as quality_issue,
  concat_ws(
    ' | ',
    'entered=' || coalesce(to_varchar(date_entered), 'NULL'),
    'disposition=' || coalesce(to_varchar(disposition_date), 'NULL')
  ) as source_value,
  source_dataset_id,
  ingested_at
from {{ ref('fct_complaints') }}
where coalesce(resolution_date_anomaly, false)

union all

select
  'violations' as domain,
  violation_key::varchar as record_key,
  'ISSUE_DATE_PARSE_FAILED' as quality_issue,
  source_issue_date as source_value,
  source_dataset_id,
  ingested_at
from {{ ref('fct_violations') }}
where issue_date_parse_failed
