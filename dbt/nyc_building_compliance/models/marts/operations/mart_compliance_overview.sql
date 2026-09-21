with building_metrics as (
  select
    snapshot_date,
    count(*) as observed_building_count,
    count_if(total_open_compliance_item_count > 0) as building_with_open_item_count,
    count_if(attention_tier in ('CRITICAL', 'HIGH')) as priority_building_count,
    sum(open_complaint_count) as open_complaint_count,
    sum(open_violation_count) as open_violation_count,
    sum(active_permit_record_count) as active_permit_record_count,
    sum(total_open_compliance_item_count) as total_open_compliance_item_count,
    max(attention_score) as highest_attention_score
  from {{ ref('mart_building_compliance_current') }}
  group by snapshot_date
),

complaint_resolution as (
  select
    b.snapshot_date,
    median(c.resolution_days) as median_complaint_resolution_days_12m,
    count(*) as resolved_complaint_count_12m
  from building_metrics b
  inner join {{ ref('fct_complaints') }} c
    on c.disposition_date between dateadd('day', -365, b.snapshot_date) and b.snapshot_date
  where not c.is_open
    and not coalesce(c.resolution_date_anomaly, false)
    and c.resolution_days is not null
  group by b.snapshot_date
)

select
  b.*,
  r.median_complaint_resolution_days_12m,
  coalesce(r.resolved_complaint_count_12m, 0) as resolved_complaint_count_12m
from building_metrics b
left join complaint_resolution r using (snapshot_date)
