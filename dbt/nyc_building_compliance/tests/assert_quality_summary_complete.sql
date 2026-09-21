select
  count(*) as row_count,
  count(distinct domain) as distinct_domain_count
from {{ ref('audit_data_quality_summary') }}
having count(*) != 3 or count(distinct domain) != 3
