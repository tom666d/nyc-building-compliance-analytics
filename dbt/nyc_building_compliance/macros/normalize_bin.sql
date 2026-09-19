{% macro normalize_bin(expression) %}
  case
    when regexp_like(trim({{ expression }}::varchar), '^[0-9]{7}$')
      then trim({{ expression }}::varchar)
    else null
  end
{% endmacro %}
