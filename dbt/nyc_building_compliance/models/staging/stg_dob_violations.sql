with ranked as (
  select *, row_number() over (
    partition by raw_payload:isn_dob_bis_viol::varchar order by ingested_at desc
  ) as row_num
  from {{ source('dob_raw', 'violations') }}
)
select
  raw_payload:isn_dob_bis_viol::varchar as violation_key,
  raw_payload:isn_dob_bis_viol::varchar as source_violation_id,
  {{ normalize_bin('raw_payload:bin') }} as bin,
  upper(trim(raw_payload:boro::varchar)) as borough,
  trim(raw_payload:house_number::varchar) as house_number,
  upper(trim(raw_payload:street::varchar)) as street_name,
  raw_payload:violation_number::varchar as violation_number,
  raw_payload:violation_type_code::varchar as violation_type_code,
  raw_payload:description::varchar as violation_description,
  try_to_date(raw_payload:issue_date::varchar) as issue_date,
  try_to_date(raw_payload:disposition_date::varchar) as disposition_date,
  raw_payload:disposition_comments::varchar as disposition_comments,
  source_dataset_id,
  source_row_hash,
  ingested_at
from ranked
where row_num = 1
