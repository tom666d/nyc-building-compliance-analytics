with violations as (
  select
    *,
    case
      when upper(trim(violation_category)) like '%ACTIVE%' then 'ACTIVE'
      when upper(trim(violation_category)) like '%RESOLVED%' then 'RESOLVED'
      when upper(trim(violation_category)) like '%DISMISSED%' then 'DISMISSED'
      else 'UNKNOWN'
    end as violation_status_group
  from {{ ref('stg_dob_violations') }}
)

select
  v.violation_key,
  b.building_key,
  v.bin,
  v.source_violation_id,
  v.violation_number,
  v.violation_type_code,
  v.violation_category,
  v.violation_status_group,
  v.violation_status_group = 'ACTIVE' as is_open,
  v.violation_status_group = 'UNKNOWN' as is_status_unmapped,
  v.violation_description,
  v.source_issue_date,
  v.issue_date,
  v.issue_date_parse_failed,
  v.disposition_date,
  v.disposition_comments,
  v.source_dataset_id,
  v.source_row_hash,
  v.source_load_id,
  v.ingested_at
from violations v
left join {{ ref('dim_buildings') }} b using (bin)
