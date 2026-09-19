select c.complaint_key, b.building_key, c.complaint_number, c.complaint_category,
       c.complaint_status, c.date_entered, c.inspection_date, c.disposition_date,
       c.disposition_code,
       datediff('day', c.date_entered, c.disposition_date) as resolution_days,
       c.complaint_status != 'CLOSED' as is_open,
       c.source_dataset_id, c.ingested_at
from {{ ref('stg_dob_complaints') }} c
left join {{ ref('dim_buildings') }} b using (bin)
