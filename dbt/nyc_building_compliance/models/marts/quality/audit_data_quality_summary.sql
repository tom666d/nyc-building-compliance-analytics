with domain_metrics as (
  select
    'permit_records' as domain,
    count(*) as total_record_count,
    count_if(building_key is null) as missing_building_key_count,
    count_if(is_status_unmapped) as unmapped_status_count,
    count_if(coalesce(approval_to_issue_date_anomaly, false)) as date_anomaly_count
  from {{ ref('fct_permit_records') }}

  union all

  select
    'complaints' as domain,
    count(*) as total_record_count,
    count_if(building_key is null) as missing_building_key_count,
    count_if(is_status_unmapped) as unmapped_status_count,
    count_if(coalesce(resolution_date_anomaly, false)) as date_anomaly_count
  from {{ ref('fct_complaints') }}

  union all

  select
    'violations' as domain,
    count(*) as total_record_count,
    count_if(building_key is null) as missing_building_key_count,
    count_if(is_status_unmapped) as unmapped_status_count,
    count_if(issue_date_parse_failed) as date_anomaly_count
  from {{ ref('fct_violations') }}
),

source_freshness as (
  select
    'permit_records' as domain,
    max(ingested_at) as source_last_ingested_at
  from {{ source('dob_raw', 'permits') }}

  union all

  select
    'complaints' as domain,
    max(ingested_at) as source_last_ingested_at
  from {{ source('dob_raw', 'complaints') }}

  union all

  select
    'violations' as domain,
    max(ingested_at) as source_last_ingested_at
  from {{ source('dob_raw', 'violations') }}
),

measured as (
  select
    current_timestamp() as measured_at,
    m.domain,
    m.total_record_count,
    m.total_record_count - m.missing_building_key_count as matched_building_key_count,
    m.missing_building_key_count,
    round(
      100.0 * (m.total_record_count - m.missing_building_key_count)
        / nullif(m.total_record_count, 0),
      2
    ) as building_key_coverage_pct,
    m.unmapped_status_count,
    m.date_anomaly_count,
    m.missing_building_key_count + m.unmapped_status_count + m.date_anomaly_count
      as issue_indicator_count,
    f.source_last_ingested_at,
    datediff('hour', f.source_last_ingested_at, current_timestamp()) as source_age_hours,
    {{ var('minimum_building_key_coverage_pct', 99.0) }}::number(5, 2)
      as minimum_building_key_coverage_pct
  from domain_metrics m
  inner join source_freshness f using (domain)
)

select
  *,
  case
    when total_record_count = 0 then 'ERROR'
    when source_age_hours > 72 then 'ERROR'
    when building_key_coverage_pct < minimum_building_key_coverage_pct then 'ERROR'
    when unmapped_status_count > 0 then 'ERROR'
    when source_age_hours > 36 then 'WARN'
    when missing_building_key_count > 0 then 'WARN'
    when date_anomaly_count > 0 then 'WARN'
    else 'PASS'
  end as quality_status
from measured
