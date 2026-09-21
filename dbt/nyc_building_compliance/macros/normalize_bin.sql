{% macro normalize_bin(expression) %}
  case
    when regexp_like(trim({{ expression }}::varchar), '^[1-5][0-9]{6}$')
      and not regexp_like(trim({{ expression }}::varchar), '^[1-5]0{6}$')
      then trim({{ expression }}::varchar)
    else null
  end
{% endmacro %}
