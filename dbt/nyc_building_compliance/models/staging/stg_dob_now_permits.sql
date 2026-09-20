with exact_payloads as (
  select
    *,
    row_number() over (
      partition by source_row_hash
      order by ingested_at desc, load_id desc
    ) as payload_row_num
  from {{ source('dob_raw', 'permits') }}
)

select
  source_row_hash as permit_key,
  raw_payload:job_filing_number::varchar as job_filing_number,
  raw_payload:tracking_number::varchar as tracking_number,
  raw_payload:work_permit::varchar as work_permit,
  raw_payload:sequence_number::varchar as sequence_number,
  {{ normalize_bin('raw_payload:bin') }} as bin,
  raw_payload:bbl::varchar as bbl,
  {{ normalize_borough('raw_payload:borough') }} as borough,
  trim(raw_payload:house_no::varchar) as house_number,
  upper(trim(raw_payload:street_name::varchar)) as street_name,
  raw_payload:work_type::varchar as work_type,
  upper(trim(raw_payload:permit_status::varchar)) as permit_status,
  to_date(try_to_timestamp_ntz(raw_payload:approved_date::varchar)) as approved_date,
  to_date(try_to_timestamp_ntz(raw_payload:issued_date::varchar)) as issued_date,
  to_date(try_to_timestamp_ntz(raw_payload:expired_date::varchar)) as expired_date,
  try_to_decimal(raw_payload:estimated_job_costs::varchar, 18, 2) as estimated_job_cost,
  raw_payload:job_description::varchar as job_description,
  source_dataset_id,
  source_row_hash,
  load_id as source_load_id,
  ingested_at
from exact_payloads
where payload_row_num = 1
