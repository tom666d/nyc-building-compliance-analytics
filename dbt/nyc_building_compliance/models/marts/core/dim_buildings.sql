with observations as (
  select
    *,
    case
      when regexp_like(trim(bbl), '^[0-9]{10}$') then trim(bbl)
    end as validated_bbl
  from {{ ref('int_building_observations') }}
),

ranked as (
  select
    *,
    row_number() over (
      partition by bin
      order by
        (validated_bbl is not null) desc,
        (borough is not null) desc,
        (house_number is not null and street_name is not null) desc,
        source_priority,
        ingested_at desc
    ) as row_num
  from observations
),

source_rollup as (
  select
    bin,
    max(ingested_at) as source_last_observed_at,
    count(distinct record_source) as observed_source_count
  from observations
  group by bin
)

select
  {{ dbt_utils.generate_surrogate_key(['r.bin']) }} as building_key,
  r.bin,
  r.validated_bbl as bbl,
  r.borough,
  r.house_number,
  r.street_name,
  nullif(trim(concat_ws(' ', r.house_number, r.street_name)), '') as display_address,
  r.record_source as selected_attribute_source,
  s.source_last_observed_at,
  s.observed_source_count
from ranked r
inner join source_rollup s using (bin)
where r.row_num = 1
