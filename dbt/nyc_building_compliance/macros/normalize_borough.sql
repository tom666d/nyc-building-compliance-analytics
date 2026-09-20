{% macro normalize_borough(expression) %}
  case upper(trim({{ expression }}::varchar))
    when '1' then 'MANHATTAN'
    when 'MN' then 'MANHATTAN'
    when 'MANHATTAN' then 'MANHATTAN'
    when '2' then 'BRONX'
    when 'BX' then 'BRONX'
    when 'BRONX' then 'BRONX'
    when '3' then 'BROOKLYN'
    when 'BK' then 'BROOKLYN'
    when 'BROOKLYN' then 'BROOKLYN'
    when '4' then 'QUEENS'
    when 'QN' then 'QUEENS'
    when 'QUEENS' then 'QUEENS'
    when '5' then 'STATEN ISLAND'
    when 'SI' then 'STATEN ISLAND'
    when 'STATEN ISLAND' then 'STATEN ISLAND'
    else null
  end
{% endmacro %}
