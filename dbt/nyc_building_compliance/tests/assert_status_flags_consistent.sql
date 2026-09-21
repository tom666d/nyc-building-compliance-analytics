select
  'permit_records' as domain,
  permit_key::varchar as record_key,
  permit_status_group as status_group
from {{ ref('fct_permit_records') }}
where
  is_issued_record != (permit_status_group = 'ISSUED')
  or is_status_unmapped != (permit_status_group = 'UNKNOWN')

union all

select
  'complaints' as domain,
  complaint_key::varchar as record_key,
  complaint_status_group as status_group
from {{ ref('fct_complaints') }}
where
  is_open != (complaint_status_group = 'ACTIVE')
  or is_status_unmapped != (complaint_status_group = 'UNKNOWN')

union all

select
  'violations' as domain,
  violation_key::varchar as record_key,
  violation_status_group as status_group
from {{ ref('fct_violations') }}
where
  is_open != (violation_status_group = 'ACTIVE')
  or is_status_unmapped != (violation_status_group = 'UNKNOWN')
