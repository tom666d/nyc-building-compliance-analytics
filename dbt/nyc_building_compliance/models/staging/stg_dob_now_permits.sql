with ranked as (
  select *, row_number() over (
    partition by raw_payload:job_filing_number::varchar,
                 raw_payload:work_permit::varchar,
                 raw_payload:sequence_number::varchar
    order by ingested_at desc
  ) as row_num
  from {{ source('dob_raw', 'permits') }}
)
select
  {{ dbt_utils.generate_surrogate_key([
    "raw_payload:job_filing_number::varchar",
    "raw_payload:work_permit::varchar",
    "raw_payload:sequence_number::varchar"
  ]) }} as permit_key,
  raw_payload:job_filing_number::varchar as job_filing_number,
  raw_payload:work_permit::varchar as work_permit,
  raw_payload:sequence_number::varchar as sequence_number,
  {{ normalize_bin('raw_payload:bin') }} as bin,
  raw_payload:bbl::varchar as bbl,
  upper(trim(raw_payload:borough::varchar)) as borough,
  trim(raw_payload:house_no::varchar) as house_number,
  upper(trim(raw_payload:street_name::varchar)) as street_name,
  raw_payload:work_type::varchar as work_type,
  upper(trim(raw_payload:permit_status::varchar)) as permit_status,
  try_to_date(raw_payload:approved_date::varchar) as approved_date,
  try_to_date(raw_payload:issued_date::varchar) as issued_date,
  try_to_date(raw_payload:expired_date::varchar) as expired_date,
  try_to_decimal(raw_payload:estimated_job_costs::varchar, 18, 2) as estimated_job_cost,
  raw_payload:job_description::varchar as job_description,
  source_dataset_id,
  source_row_hash,
  ingested_at
from ranked
where row_num = 1
