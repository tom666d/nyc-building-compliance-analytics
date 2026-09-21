with duplicate_load_records as (
  select
    'permits' as domain,
    source_row_hash,
    load_id,
    count(*) as record_count
  from {{ source('dob_raw', 'permits') }}
  group by source_row_hash, load_id
  having count(*) > 1

  union all

  select
    'complaints' as domain,
    source_row_hash,
    load_id,
    count(*) as record_count
  from {{ source('dob_raw', 'complaints') }}
  group by source_row_hash, load_id
  having count(*) > 1

  union all

  select
    'violations' as domain,
    source_row_hash,
    load_id,
    count(*) as record_count
  from {{ source('dob_raw', 'violations') }}
  group by source_row_hash, load_id
  having count(*) > 1
)

select *
from duplicate_load_records
