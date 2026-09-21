select
  'permit_records' as domain,
  permit_key::varchar as record_key,
  'ISSUED_BEFORE_APPROVED' as quality_issue
from {{ ref('fct_permit_records') }}
where coalesce(approval_to_issue_date_anomaly, false)

union all

select
  'complaints' as domain,
  complaint_key::varchar as record_key,
  'DISPOSITION_BEFORE_ENTERED' as quality_issue
from {{ ref('fct_complaints') }}
where coalesce(resolution_date_anomaly, false)
