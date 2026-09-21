{% test not_null_proportion_at_least(model, column_name, minimum_proportion) %}

with coverage as (
  select
    count(*) as total_record_count,
    count_if({{ column_name }} is not null) as populated_record_count
  from {{ model }}
)

select
  total_record_count,
  populated_record_count,
  populated_record_count / nullif(total_record_count, 0) as populated_proportion,
  {{ minimum_proportion }} as required_proportion
from coverage
where
  total_record_count = 0
  or populated_record_count / nullif(total_record_count, 0) < {{ minimum_proportion }}

{% endtest %}
