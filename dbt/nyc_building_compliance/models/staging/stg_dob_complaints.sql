with ranked as (
  select *, row_number() over (
    partition by raw_payload:complaint_number::varchar order by ingested_at desc
  ) as row_num
  from {{ source('dob_raw', 'complaints') }}
)
select
  raw_payload:complaint_number::varchar as complaint_key,
  raw_payload:complaint_number::varchar as complaint_number,
  {{ normalize_bin('raw_payload:bin') }} as bin,
  upper(trim(raw_payload:borough::varchar)) as borough,
  trim(raw_payload:house_number::varchar) as house_number,
  upper(trim(raw_payload:house_street::varchar)) as street_name,
  raw_payload:complaint_category::varchar as complaint_category,
  upper(trim(raw_payload:status::varchar)) as complaint_status,
  try_to_date(raw_payload:date_entered::varchar) as date_entered,
  try_to_date(raw_payload:inspection_date::varchar) as inspection_date,
  try_to_date(raw_payload:disposition_date::varchar) as disposition_date,
  raw_payload:disposition_code::varchar as disposition_code,
  source_dataset_id,
  source_row_hash,
  ingested_at
from ranked
where row_num = 1
