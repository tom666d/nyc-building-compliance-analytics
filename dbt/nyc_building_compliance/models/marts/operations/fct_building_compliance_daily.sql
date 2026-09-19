with complaints as (
  select building_key,
         count_if(is_open) as open_complaint_count,
         min(case when is_open then date_entered end) as oldest_open_complaint_date,
         count_if(date_entered >= dateadd('day', -30, current_date)) as complaints_last_30_days
  from {{ ref('fct_complaints') }} where building_key is not null group by 1
), violations as (
  select building_key,
         count_if(is_open) as open_violation_count,
         min(case when is_open then issue_date end) as oldest_open_violation_date
  from {{ ref('fct_violations') }} where building_key is not null group by 1
), permits as (
  select building_key,
         count_if(permit_status in ('ISSUED', 'PERMIT-ENTIRE', 'PERMIT-PARTIAL')
                  and coalesce(expired_date, '9999-12-31'::date) >= current_date) as active_permit_count,
         max(issued_date) as latest_permit_issued_date
  from {{ ref('fct_permits') }} where building_key is not null group by 1
)
select
  current_date as snapshot_date,
  b.building_key,
  coalesce(c.open_complaint_count, 0) as open_complaint_count,
  coalesce(v.open_violation_count, 0) as open_violation_count,
  coalesce(p.active_permit_count, 0) as active_permit_count,
  c.oldest_open_complaint_date,
  v.oldest_open_violation_date,
  p.latest_permit_issued_date,
  coalesce(c.complaints_last_30_days, 0) as complaints_last_30_days,
  c.building_key is not null as has_complaint_history,
  v.building_key is not null as has_violation_history,
  p.building_key is not null as has_permit_history
from {{ ref('dim_buildings') }} b
left join complaints c using (building_key)
left join violations v using (building_key)
left join permits p using (building_key)
