# Business intelligence consumption layer

Building Compliance 360 is the final consumption layer for the analytics platform. It turns
governed dbt marts into a decision-oriented interface without placing Snowflake credentials in
the browser or requiring a warehouse to run for every page view.

## Product question

The dashboard is designed for an operations or compliance user who needs to answer:

1. How much unresolved workload exists in the observed source slice?
2. Which boroughs contain that workload?
3. Which buildings should be reviewed first under a transparent prioritization rule?
4. Can the user trust the source coverage and latest build evidence?

It is not a structural-safety assessment, a legal compliance determination, or a citywide
population estimate.

## Consumption architecture

```text
event facts + conformed building dimension
                 |
                 v
daily building snapshot
                 |
                 v
current building mart -> borough mart -> executive overview mart
                 |              |                  |
                 +--------------+------------------+
                                |
                                v
                  versioned JSON data contract
                                |
                                v
             Building Compliance 360 dashboard
```

Metric logic remains in dbt. The website formats, filters, and explains governed values but does
not redefine open status, building identity, resolution time, or prioritization thresholds.

## Published consumption marts

| Model | Grain | Purpose |
|---|---|---|
| `mart_building_compliance_current` | One row per building in the latest snapshot | Building queue, drill-through, and transparent attention score |
| `mart_borough_compliance_current` | One row per borough in the latest snapshot | Geographic workload comparison and priority-building rate |
| `mart_compliance_overview` | One row for the latest snapshot | Executive key performance indicators and trailing-365-day resolution metric |

All three models are physical Snowflake tables in the development mart schema. They are included
in the `building_compliance_360` dbt exposure so the lineage graph connects source data to the
named user-facing product.

## Attention score

The queue uses a reproducible workload score:

```text
open complaints × 4
+ open violations × 6
+ complaints entered in the last 30 days × 2
+ oldest-open-item age bonus
= attention score, capped at 100
```

Age bonus:

- 365 days or older: 10 points;
- 180–364 days: 7 points;
- 90–179 days: 4 points;
- less than 90 days or no open item: 0 points.

Tiers:

- `CRITICAL`: 50–100;
- `HIGH`: 20–49;
- `MODERATE`: 10–19;
- `LOW`: 0–9.

This is deliberately named an **attention score**, not a risk score. The retained legacy
violation source does not provide a governed severity classification, and the score must not imply
structural danger or legal priority. Its only purpose is to make an operations review queue
consistent and explainable.

## Versioned snapshot contract

`scripts/export_dashboard_data.py` reads the marts with the least-privilege reader role and writes
`dashboard/data/dashboard-snapshot.json`. The export contains:

- snapshot and export metadata;
- source-scope and normalization disclosures;
- executive metrics;
- borough metrics;
- attention-tier distribution;
- the bounded priority-building queue; and
- source-domain quality status.

The website imports that file at build time. Snowflake credentials are never bundled into client
code, and a page view does not resume a warehouse. This makes the published product cheap,
repeatable, and safe to share. It also means the deployed view is as current as its last explicit
export rather than a live operational dashboard.

`dashboard/scripts/validate-dashboard-data.mjs` blocks a build when the contract is internally
inconsistent. It verifies borough rollups against the overview, attention-tier totals, allowed
quality statuses, unique and usable Building Identification Numbers, and open-item arithmetic.

## Dashboard views

### Overview

- priority-building count;
- open complaint and violation workload;
- trailing-365-day median complaint resolution time;
- open-item comparison by borough;
- attention-tier distribution; and
- ranked priority-building table.

### Building explorer

- search by address, Building Identification Number, or borough;
- current attention score and tier;
- complaint and violation components;
- age of the oldest retained open item; and
- an explanation of why the row is prioritized.

### Data quality

- record count and building-key coverage for each source domain;
- `PASS`, `WARN`, or `ERROR` status from the governed audit model;
- dbt build evidence for the consumption marts; and
- visible source-scope and normalization limitations.

## Deployment

The validated dashboard is deployed at
[NYC Building Compliance 360](https://nyc-building-compliance-360-portfolio.hsieh203.chatgpt.site).
It is access-controlled by default. The application artifact, data release, and audience setting
are managed independently, so public access can be enabled without exposing warehouse credentials.

## Real-data evidence

On 2026-09-21, dbt created the three consumption marts in Snowflake and ran their selected
downstream graph:

```text
3 table models created
18 data tests passed
1 dashboard exposure resolved
PASS=21, WARN=0, ERROR=0, NO-OP=1
```

The resulting bounded snapshot represents 1,000 source records from each of the three official
NYC Open Data datasets. Its latest daily snapshot date is 2026-09-20.

The first dashboard profile exposed an all-zero `0000000` value that had passed the original
seven-digit regular expression and accumulated eleven legacy violation records under a false
building. NYC documentation defines the first digit of a usable Building Identification Number
as its borough code. The normalization rule now requires a first digit from one through five and
rejects borough-zero placeholders. The checked-in dashboard snapshot reconciles the published
aggregate by excluding that pseudo-building.

The subsequent Snowflake rebuild is pending because the monthly resource monitor reached its
configured quota and correctly prevented the warehouse from resuming. The quota was not raised or
bypassed. This boundary is recorded instead of presenting the post-fix warehouse state as already
verified.

## Cost and security controls

- The browser receives no Snowflake account name, user, private key, password, or role.
- Snapshot refresh uses the least-privilege reader identity.
- Normal page views have no Snowflake cost.
- The source slice remains bounded and prominently disclosed.
- The Snowflake resource monitor stopped additional compute when its monthly quota was reached.
- The production dependency audit reports zero known vulnerabilities in runtime packages.
- GitHub static CI validates the snapshot contract, application lint, production dependency
  audit, and optimized build without external credentials.

## Known limitations

- The source slice is bounded to 1,000 rows per domain and is not statistically representative of
  all New York City buildings.
- Only one daily snapshot exists, so the product does not display a fabricated historical trend.
- The priority queue is a workload heuristic, not a trained model or official severity system.
- The exported site is static and requires a deliberate refresh after the warehouse is rebuilt.
- The current building explorer contains a bounded queue rather than every observed building.
- Legacy violation dates in the ordered source slice are old; they correctly influence item age
  but also demonstrate why sample selection affects interpretation.
- The post-normalization warehouse rebuild remains pending the resource-monitor reset.

## Local operation

```text
make dashboard-install   # Install the locked website dependencies
make dashboard-check     # Audit runtime packages, validate data, lint, and build
make dashboard-dev       # Run the local dashboard
make dashboard-export    # Refresh the snapshot from Snowflake when compute is available
```

## Official references

- [dbt exposures](https://docs.getdbt.com/docs/build/exposures)
- [Snowflake resource monitors](https://docs.snowflake.com/en/user-guide/resource-monitors)
- [NYC Department of Buildings BIN guide](https://www.nyc.gov/assets/buildings/pdf/article_320_guide.pdf)
- [Next.js client components](https://nextjs.org/docs/app/getting-started/server-and-client-components)
- [Node.js package-lock files](https://docs.npmjs.com/cli/configuring-npm/package-lock-json)
- [npm audit](https://docs.npmjs.com/cli/commands/npm-audit)
