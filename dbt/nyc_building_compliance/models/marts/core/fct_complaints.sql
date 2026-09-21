with complaints as (
  select
    *,
    case
      when complaint_status = 'ACTIVE' then 'ACTIVE'
      when complaint_status = 'CLOSED' then 'RESOLVED'
      else 'UNKNOWN'
    end as complaint_status_group
  from {{ ref('stg_dob_complaints') }}
)

select
  c.complaint_key,
  b.building_key,
  c.bin,
  c.complaint_number,
  c.complaint_category,
  c.complaint_status,
  c.complaint_status_group,
  c.complaint_status_group = 'ACTIVE' as is_open,
  c.complaint_status_group = 'UNKNOWN' as is_status_unmapped,
  c.date_entered,
  c.inspection_date,
  c.disposition_date,
  c.disposition_code,
  datediff('day', c.date_entered, c.disposition_date) as resolution_days,
  c.disposition_date < c.date_entered as resolution_date_anomaly,
  c.source_dataset_id,
  c.source_row_hash,
  c.source_load_id,
  c.ingested_at
from complaints c
left join {{ ref('dim_buildings') }} b using (bin)
