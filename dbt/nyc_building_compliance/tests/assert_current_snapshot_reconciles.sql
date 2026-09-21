with expected as (
  select
    (select count(*) from {{ ref('dim_buildings') }}) as building_count,
    (
      select count_if(building_key is not null and complaint_status_group = 'ACTIVE')
      from {{ ref('fct_complaints') }}
    ) as open_complaint_count,
    (
      select count_if(building_key is not null and violation_status_group = 'ACTIVE')
      from {{ ref('fct_violations') }}
    ) as open_violation_count,
    (
      select count_if(
        building_key is not null
        and permit_status_group = 'ISSUED'
        and coalesce(expired_date, '9999-12-31'::date) >= current_date
      )
      from {{ ref('fct_permit_records') }}
    ) as active_permit_record_count,
    (
      select count_if(
        building_key is not null
        and date_entered >= dateadd('day', -30, current_date)
      )
      from {{ ref('fct_complaints') }}
    ) as complaints_last_30_days
),

actual as (
  select
    count(*) as building_count,
    sum(open_complaint_count) as open_complaint_count,
    sum(open_violation_count) as open_violation_count,
    sum(active_permit_record_count) as active_permit_record_count,
    sum(complaints_last_30_days) as complaints_last_30_days
  from {{ ref('fct_building_compliance_daily') }}
  where snapshot_date = current_date
)

select
  e.building_count as expected_building_count,
  a.building_count as actual_building_count,
  e.open_complaint_count as expected_open_complaint_count,
  a.open_complaint_count as actual_open_complaint_count,
  e.open_violation_count as expected_open_violation_count,
  a.open_violation_count as actual_open_violation_count,
  e.active_permit_record_count as expected_active_permit_record_count,
  a.active_permit_record_count as actual_active_permit_record_count,
  e.complaints_last_30_days as expected_complaints_last_30_days,
  a.complaints_last_30_days as actual_complaints_last_30_days
from expected e
cross join actual a
where
  e.building_count != a.building_count
  or e.open_complaint_count != coalesce(a.open_complaint_count, -1)
  or e.open_violation_count != coalesce(a.open_violation_count, -1)
  or e.active_permit_record_count != coalesce(a.active_permit_record_count, -1)
  or e.complaints_last_30_days != coalesce(a.complaints_last_30_days, -1)
