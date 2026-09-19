select v.violation_key, b.building_key, v.source_violation_id, v.violation_number,
       v.violation_type_code, v.violation_description, v.issue_date, v.disposition_date,
       v.disposition_comments, v.disposition_date is null as is_open,
       v.source_dataset_id, v.ingested_at
from {{ ref('stg_dob_violations') }} v
left join {{ ref('dim_buildings') }} b using (bin)
