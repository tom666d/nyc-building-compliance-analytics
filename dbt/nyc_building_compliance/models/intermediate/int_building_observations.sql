select bin, bbl, borough, house_number, street_name, ingested_at, 'permit' as record_source
from {{ ref('stg_dob_now_permits') }} where bin is not null
union all
select bin, null as bbl, borough, house_number, street_name, ingested_at, 'complaint'
from {{ ref('stg_dob_complaints') }} where bin is not null
union all
select bin, null as bbl, borough, house_number, street_name, ingested_at, 'violation'
from {{ ref('stg_dob_violations') }} where bin is not null
