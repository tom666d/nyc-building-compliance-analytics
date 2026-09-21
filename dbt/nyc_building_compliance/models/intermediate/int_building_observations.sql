select
  bin,
  bbl,
  borough,
  nullif(trim(house_number), '') as house_number,
  nullif(trim(street_name), '') as street_name,
  ingested_at,
  'permit' as record_source,
  1 as source_priority
from {{ ref('stg_dob_now_permits') }}
where bin is not null

union all

select
  bin,
  null as bbl,
  borough,
  nullif(trim(house_number), '') as house_number,
  nullif(trim(street_name), '') as street_name,
  ingested_at,
  'complaint' as record_source,
  2 as source_priority
from {{ ref('stg_dob_complaints') }}
where bin is not null

union all

select
  bin,
  null as bbl,
  borough,
  nullif(trim(house_number), '') as house_number,
  nullif(trim(street_name), '') as street_name,
  ingested_at,
  'violation' as record_source,
  3 as source_priority
from {{ ref('stg_dob_violations') }}
where bin is not null
