with exact_payloads as (
  select
    *,
    row_number() over (
      partition by source_row_hash
      order by ingested_at desc, load_id desc
    ) as payload_row_num
  from {{ source('dob_raw', 'violations') }}
), latest_business_record as (
  select
    *,
    row_number() over (
      partition by raw_payload:isn_dob_bis_viol::varchar
      order by ingested_at desc, source_row_hash desc
    ) as business_row_num
  from exact_payloads
  where payload_row_num = 1
)

select
  raw_payload:isn_dob_bis_viol::varchar as violation_key,
  raw_payload:isn_dob_bis_viol::varchar as source_violation_id,
  {{ normalize_bin('raw_payload:bin') }} as bin,
  {{ normalize_borough('raw_payload:boro') }} as borough,
  trim(raw_payload:house_number::varchar) as house_number,
  upper(trim(raw_payload:street::varchar)) as street_name,
  raw_payload:violation_number::varchar as violation_number,
  raw_payload:violation_type_code::varchar as violation_type_code,
  raw_payload:violation_category::varchar as violation_category,
  raw_payload:description::varchar as violation_description,
  raw_payload:issue_date::varchar as source_issue_date,
  case
    when regexp_like(raw_payload:issue_date::varchar, '^(19|20)[0-9]{6}$')
      then try_to_date(raw_payload:issue_date::varchar, 'YYYYMMDD')
  end as issue_date,
  iff(
    raw_payload:issue_date is not null
    and (
      not regexp_like(raw_payload:issue_date::varchar, '^(19|20)[0-9]{6}$')
      or try_to_date(raw_payload:issue_date::varchar, 'YYYYMMDD') is null
    ),
    true,
    false
  ) as issue_date_parse_failed,
  try_to_date(raw_payload:disposition_date::varchar, 'YYYYMMDD') as disposition_date,
  raw_payload:disposition_comments::varchar as disposition_comments,
  source_dataset_id,
  source_row_hash,
  load_id as source_load_id,
  ingested_at
from latest_business_record
where business_row_num = 1
