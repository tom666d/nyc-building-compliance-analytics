{{
  config(
    materialized='incremental',
    unique_key=['snapshot_date', 'building_key'],
    incremental_strategy='merge',
    on_schema_change='sync_all_columns'
  )
}}

with run_context as (
  select current_date as snapshot_date
),

complaints as (
  select
    c.building_key,
    count_if(c.is_open) as open_complaint_count,
    min(case when c.is_open then c.date_entered end) as oldest_open_complaint_date,
    count_if(c.date_entered >= dateadd('day', -30, r.snapshot_date)) as complaints_last_30_days,
    count_if(c.is_status_unmapped) as unmapped_complaint_status_count
  from {{ ref('fct_complaints') }} c
  cross join run_context r
  where c.building_key is not null
  group by c.building_key
),

violations as (
  select
    building_key,
    count_if(is_open) as open_violation_count,
    min(case when is_open then issue_date end) as oldest_open_violation_date,
    count_if(is_status_unmapped) as unmapped_violation_status_count
  from {{ ref('fct_violations') }}
  where building_key is not null
  group by building_key
),

permits as (
  select
    p.building_key,
    count_if(
      p.permit_status_group = 'ISSUED'
      and coalesce(p.expired_date, '9999-12-31'::date) >= r.snapshot_date
    ) as active_permit_record_count,
    max(p.issued_date) as latest_permit_issued_date,
    count_if(p.is_status_unmapped) as unmapped_permit_status_count
  from {{ ref('fct_permit_records') }} p
  cross join run_context r
  where p.building_key is not null
  group by p.building_key
)

select
  r.snapshot_date,
  b.building_key,
  coalesce(c.open_complaint_count, 0) as open_complaint_count,
  coalesce(v.open_violation_count, 0) as open_violation_count,
  coalesce(p.active_permit_record_count, 0) as active_permit_record_count,
  c.oldest_open_complaint_date,
  v.oldest_open_violation_date,
  p.latest_permit_issued_date,
  coalesce(c.complaints_last_30_days, 0) as complaints_last_30_days,
  coalesce(c.unmapped_complaint_status_count, 0) as unmapped_complaint_status_count,
  coalesce(v.unmapped_violation_status_count, 0) as unmapped_violation_status_count,
  coalesce(p.unmapped_permit_status_count, 0) as unmapped_permit_status_count,
  c.building_key is not null as has_complaint_history,
  v.building_key is not null as has_violation_history,
  p.building_key is not null as has_permit_history
from {{ ref('dim_buildings') }} b
cross join run_context r
left join complaints c using (building_key)
left join violations v using (building_key)
left join permits p using (building_key)
