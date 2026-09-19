with ranked as (
  select *, row_number() over (
    partition by bin
    order by (bbl is not null) desc, ingested_at desc, record_source
  ) as row_num
  from {{ ref('int_building_observations') }}
)
select
  {{ dbt_utils.generate_surrogate_key(['bin']) }} as building_key,
  bin,
  bbl,
  borough,
  house_number,
  street_name,
  concat_ws(' ', house_number, street_name) as display_address,
  record_source as selected_attribute_source,
  ingested_at as source_last_observed_at
from ranked
where row_num = 1
