with latest_snapshot as (
  select max(snapshot_date) as snapshot_date
  from {{ ref('fct_building_compliance_daily') }}
),

current_buildings as (
  select
    s.snapshot_date,
    s.building_key,
    b.bin,
    b.bbl,
    b.borough,
    b.display_address,
    b.observed_source_count,
    s.open_complaint_count,
    s.open_violation_count,
    s.active_permit_record_count,
    s.open_complaint_count + s.open_violation_count as total_open_compliance_item_count,
    s.complaints_last_30_days,
    case
      when s.oldest_open_complaint_date is null then s.oldest_open_violation_date
      when s.oldest_open_violation_date is null then s.oldest_open_complaint_date
      else least(s.oldest_open_complaint_date, s.oldest_open_violation_date)
    end as oldest_open_item_date,
    s.latest_permit_issued_date,
    s.unmapped_complaint_status_count
      + s.unmapped_violation_status_count
      + s.unmapped_permit_status_count as status_mapping_exception_count,
    s.has_complaint_history,
    s.has_violation_history,
    s.has_permit_history
  from {{ ref('fct_building_compliance_daily') }} s
  inner join latest_snapshot l using (snapshot_date)
  inner join {{ ref('dim_buildings') }} b using (building_key)
),

aged as (
  select
    *,
    greatest(0, datediff('day', oldest_open_item_date, snapshot_date))
      as oldest_open_item_age_days
  from current_buildings
),

scored as (
  select
    *,
    least(
      100,
      open_complaint_count * 4
        + open_violation_count * 6
        + complaints_last_30_days * 2
        + case
          when oldest_open_item_age_days >= 365 then 10
          when oldest_open_item_age_days >= 180 then 7
          when oldest_open_item_age_days >= 90 then 4
          else 0
        end
    ) as attention_score
  from aged
)

select
  *,
  case
    when attention_score >= 50 then 'CRITICAL'
    when attention_score >= 20 then 'HIGH'
    when attention_score >= 10 then 'MODERATE'
    else 'LOW'
  end as attention_tier
from scored
