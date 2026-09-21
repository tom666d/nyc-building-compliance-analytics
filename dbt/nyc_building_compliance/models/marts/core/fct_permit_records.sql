with permits as (
  select
    *,
    case
      when permit_status = 'PERMIT ISSUED' then 'ISSUED'
      when permit_status = 'SIGNED-OFF' then 'SIGNED_OFF'
      else 'UNKNOWN'
    end as permit_status_group
  from {{ ref('stg_dob_now_permits') }}
)

select
  p.permit_key,
  b.building_key,
  p.bin,
  p.job_filing_number,
  p.tracking_number,
  p.work_permit,
  p.sequence_number,
  p.work_type,
  p.permit_status,
  p.permit_status_group,
  p.permit_status_group = 'ISSUED' as is_issued_record,
  p.permit_status_group = 'UNKNOWN' as is_status_unmapped,
  p.approved_date,
  p.issued_date,
  p.expired_date,
  datediff('day', p.approved_date, p.issued_date) as approval_to_issue_days,
  p.issued_date < p.approved_date as approval_to_issue_date_anomaly,
  p.estimated_job_cost,
  p.job_description,
  p.source_dataset_id,
  p.source_row_hash,
  p.source_load_id,
  p.ingested_at
from permits p
left join {{ ref('dim_buildings') }} b using (bin)
