select p.permit_key, b.building_key, p.job_filing_number, p.work_permit, p.sequence_number,
       p.work_type, p.permit_status, p.approved_date, p.issued_date, p.expired_date,
       datediff('day', p.approved_date, p.issued_date) as approval_to_issue_days,
       p.estimated_job_cost, p.job_description, p.source_dataset_id, p.ingested_at
from {{ ref('stg_dob_now_permits') }} p
left join {{ ref('dim_buildings') }} b using (bin)
