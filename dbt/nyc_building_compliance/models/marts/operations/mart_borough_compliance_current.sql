select
  snapshot_date,
  borough,
  count(*) as observed_building_count,
  count_if(total_open_compliance_item_count > 0) as building_with_open_item_count,
  count_if(attention_tier in ('CRITICAL', 'HIGH')) as priority_building_count,
  round(
    100.0 * count_if(attention_tier in ('CRITICAL', 'HIGH')) / nullif(count(*), 0),
    2
  ) as priority_building_rate_pct,
  sum(open_complaint_count) as open_complaint_count,
  sum(open_violation_count) as open_violation_count,
  sum(active_permit_record_count) as active_permit_record_count,
  sum(total_open_compliance_item_count) as total_open_compliance_item_count,
  max(attention_score) as highest_attention_score
from {{ ref('mart_building_compliance_current') }}
group by snapshot_date, borough
