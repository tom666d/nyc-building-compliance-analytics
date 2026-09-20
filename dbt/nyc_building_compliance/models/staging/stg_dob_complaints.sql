with exact_payloads as (
  select
    *,
    row_number() over (
      partition by source_row_hash
      order by ingested_at desc, load_id desc
    ) as payload_row_num
  from {{ source('dob_raw', 'complaints') }}
), latest_business_record as (
  select
    *,
    row_number() over (
      partition by raw_payload:complaint_number::varchar
      order by ingested_at desc, source_row_hash desc
    ) as business_row_num
  from exact_payloads
  where payload_row_num = 1
)

select
  raw_payload:complaint_number::varchar as complaint_key,
  raw_payload:complaint_number::varchar as complaint_number,
  {{ normalize_bin('raw_payload:bin') }} as bin,
  {{ normalize_borough("left(trim(raw_payload:bin::varchar), 1)") }} as borough,
  trim(raw_payload:house_number::varchar) as house_number,
  upper(trim(raw_payload:house_street::varchar)) as street_name,
  raw_payload:complaint_category::varchar as complaint_category,
  upper(trim(raw_payload:status::varchar)) as complaint_status,
  try_to_date(raw_payload:date_entered::varchar, 'MM/DD/YYYY') as date_entered,
  try_to_date(raw_payload:inspection_date::varchar, 'MM/DD/YYYY') as inspection_date,
  try_to_date(raw_payload:disposition_date::varchar, 'MM/DD/YYYY') as disposition_date,
  raw_payload:disposition_code::varchar as disposition_code,
  source_dataset_id,
  source_row_hash,
  load_id as source_load_id,
  ingested_at
from latest_business_record
where business_row_num = 1
