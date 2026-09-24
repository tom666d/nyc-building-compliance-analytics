# NYC Building Compliance & Permit Analytics Platform

[![CI](https://github.com/tom666d/nyc-building-compliance-analytics/actions/workflows/ci.yml/badge.svg)](https://github.com/tom666d/nyc-building-compliance-analytics/actions/workflows/ci.yml)

A governed decision-support platform for building compliance operations. It replaces manual
reconciliation across permit, complaint, and violation datasets with one building-level review
queue, consistent metric definitions, and visible data-quality evidence.

**Project context:** A self-directed analytics engineering project built to apply a
production-oriented extract-load-transform (ELT) workflow to real NYC Open Data.

**Core stack:** Python · SQL · Snowflake · dbt Core · Apache Airflow · GitHub Actions · Next.js ·
TypeScript

![Building Compliance 360 operational overview](docs/images/dashboard-overview.png)

*The operations overview turns separate permit, complaint, and violation records into one
borough-level workload view and an explainable building-prioritization queue.*

## Why this product matters

Building compliance information is distributed across separate New York City Department of
Buildings datasets. Each source has its own identifiers, lifecycle statuses, dates, and quality
limitations. Answering a simple question such as *"Which buildings need attention first?"*
therefore requires manual reconciliation and leaves room for teams to calculate different answers.

The underlying problem is not a lack of public data. It is the effort and ambiguity involved in
turning that data into a repeatable operational decision.

| Without the platform | Platform capability | Business value enabled |
|---|---|---|
| Search permits, complaints, and violations separately | One conformed building record across three sources | Less manual lookup and reconciliation |
| Interpret source-specific status values for every analysis | Governed definitions for open, active, and resolved records | Consistent reporting across users |
| Review an unranked list of records | Explainable attention score using unresolved workload, recency, and age | Repeatable case-review prioritization |
| Discover missing identifiers only after a metric looks wrong | Visible coverage, freshness, and exception reporting | Safer decisions and faster investigation |
| Give dashboard users direct warehouse access | Versioned, credential-free consumption contract | Lower access risk and no warehouse cost per page view |

These are value hypotheses supported by a working product and real public records, not claimed
production savings. A real deployment would measure lookup time, queue throughput, metric disputes,
and time-to-detect data-quality failures before and after adoption.

## Decision workflow

The product supports a concrete four-step compliance review:

1. **Scan the workload.** Compare unresolved complaints and violations across boroughs.
2. **Prioritize cases.** Identify buildings in the HIGH or CRITICAL attention tiers.
3. **Explain the ranking.** Review the exact unresolved-item and age components behind a score.
4. **Validate trust.** Check source coverage, refresh date, build results, and known limitations
   before acting on the data.

### Example decision from the validated sample

The current bounded release shows 27 open compliance items across 2,382 usable buildings. Manhattan
contains 16 of those observed items, and two buildings fall into the HIGH attention tier. An
operations user can move from that borough-level signal to the two buildings, see that each has two
unresolved legacy violations plus the maximum age bonus, and verify the source-quality boundary
before deciding what to review first.

This example demonstrates the decision path. Because the release contains only 1,000 records from
each source, it is not a citywide workload estimate or an official enforcement recommendation.

## Product walkthrough

### Explainable building investigation

![Building-level workload investigation](docs/images/building-explorer.png)

An operations user can search the priority queue, select a building, and see the complaint,
violation, and age components behind its attention score. The interface explains why a building
was prioritized instead of presenting an opaque risk ranking.

### Trust before action

![Source coverage and release evidence](docs/images/data-quality-monitor.png)

The quality monitor keeps source coverage, dbt release results, and interpretation limits beside
the business output. Users can see that complaint and permit records have complete building-key
coverage, while the retained violation slice carries a visible warning rather than being silently
treated as complete.

## Users and decisions

The shared analytical layer supports four recurring decisions:

| User | Decision supported | Governed evidence |
|---|---|---|
| Compliance operations | Prioritize buildings for case review | Open complaints, open violations, item age, recent activity |
| Property management | Identify unresolved building workload | Building-level compliance summary and source coverage |
| Construction operations | Monitor permit lifecycle performance | Active permit records and approval-to-issue duration |
| Analytics teams | Publish consistent reporting | Tested definitions, lineage, freshness, and quality exceptions |

## Product capabilities

**Building Compliance 360** turns three operational sources into a single decision product:

- a current building review queue with a transparent attention score;
- borough-level workload comparison;
- executive compliance and resolution metrics;
- building search by address, borough, or Building Identification Number; and
- visible source coverage, quality status, refresh date, and metric limitations.

The attention score ranks review workload; it is not a structural-safety prediction or legal risk
classification. This distinction keeps the output explainable and avoids claims the available
public data cannot support.

## Architecture

```text
Official NYC Open Data APIs
  permits | complaints | legacy violations
                  |
                  v
        Python ingestion service
     pagination | metadata | row hashes
                  |
                  v
            Snowflake RAW
                  |
                  v
       dbt staging and conformance
                  |
                  v
   dimensional facts + building dimension
                  |
                  v
      daily snapshot + quality audits
                  |
                  v
         governed consumption marts
                  |
                  v
       versioned dashboard contract
                  |
                  v
       Building Compliance 360

Apache Airflow orchestrates the warehouse path.
GitHub Actions validates code, model contracts, orchestration, and the dashboard on every change.
```

Metric logic is owned by dbt rather than duplicated in the dashboard. The web application consumes
a validated snapshot, so no Snowflake credential reaches the browser and page views do not resume
a warehouse.

## Technology stack

| Layer | Technology | Implementation |
|---|---|---|
| Source | NYC Open Data / Socrata APIs | Deterministic pagination over three official datasets |
| Ingestion | Python | Bounded loads, ingestion metadata, stable load IDs, row hashing, retry-safe merges |
| Warehouse | Snowflake | Role-separated raw, transformation, and consumption access with cost controls |
| Transformation | dbt Core | Staging, conformed dimensions, event facts, incremental snapshots, and marts |
| Data quality | dbt tests and audit models | Keys, relationships, status mappings, date logic, freshness, and coverage |
| Orchestration | Apache Airflow | Nine-task daily workflow with parallel ingestion, retries, and publication gates |
| Continuous integration | GitHub Actions | Python, dbt parsing, Airflow contract, dependency, data-contract, lint, and build checks |
| Consumption | Next.js and TypeScript | Responsive decision interface backed by a versioned JSON contract |

## Analytical model

| Model | Grain | Business purpose |
|---|---|---|
| `dim_buildings` | One validated Building Identification Number | Conformed building identity across sources |
| `fct_permit_records` | One distinct approved-permit source payload | Permit activity and lifecycle analysis |
| `fct_complaints` | One latest-state complaint | Complaint workload and resolution time |
| `fct_violations` | One latest-state legacy violation | Unresolved violation workload |
| `fct_building_compliance_daily` | One building per snapshot date | Historical, business-intelligence-ready foundation |
| `mart_building_compliance_current` | One building in the latest snapshot | Search, review queue, and attention score |
| `mart_borough_compliance_current` | One borough in the latest snapshot | Geographic workload comparison |
| `mart_compliance_overview` | One row in the latest snapshot | Executive key performance indicators |

Event facts are aggregated before they meet in the daily snapshot. This prevents a many-to-many
join across permits, complaints, and violations from multiplying business measures.

## Verified engineering evidence

The bounded validation run uses real records from three official New York City datasets; no
synthetic operational data is used.

| Evidence | Verified result |
|---|---:|
| Source records loaded | 1,000 permits + 1,000 complaints + 1,000 violations |
| Usable buildings in the published snapshot | 2,382 |
| Airflow workflow | 9 tasks completed |
| Full dbt build | 115 tests passed; 0 warnings; 0 errors |
| Consumption release | 3 marts built; 21 selected checks passed |
| Published metadata | 118 mart columns and 15 physical source columns documented |
| Continuous integration | Python, dbt, Airflow, dashboard contract, dependency audit, lint, and production build |

The checked-in dashboard snapshot is intentionally bounded and must not be interpreted as a
citywide estimate. Detailed execution evidence is recorded in
[orchestration](docs/orchestration.md), [data quality](docs/data_quality.md),
[lineage](docs/lineage.md), and [business intelligence consumption](docs/bi_consumption.md).

## Design decisions

Architecture decisions are recorded separately from implementation so reviewers can see the
trade-offs behind the code:

- [Use Building Identification Number as the canonical building key](docs/decisions/0002-building-identity.md)
- [Aggregate facts before creating the building snapshot](docs/decisions/0003-snapshot-not-wide-join.md)
- [Publish explicit status groups instead of inferring lifecycle state](docs/decisions/0006-explicit-status-groups.md)
- [Separate blocking data contracts from observable quality warnings](docs/decisions/0008-quality-severity-policy.md)
- [Orchestrate existing retry-safe commands](docs/decisions/0010-orchestrate-existing-commands-with-retry-safe-loads.md)
- [Publish a bounded, credential-free dashboard snapshot](docs/decisions/0012-publish-a-bounded-dashboard-snapshot.md)

One concrete result of this process was the discovery of the source placeholder `0000000`. It
matched the original seven-digit format check but is not a usable building identity. The revised
rule requires the first digit to be a valid borough code from one through five, and the invalid
records remain visible at event grain rather than being silently discarded.

## Operating the project

Run the same credential-free validation used by continuous integration:

```bash
make install
make ci-local
```

Run the decision interface locally:

```bash
make dashboard-install
make dashboard-check
make dashboard-dev
```

Warehouse execution requires a configured Snowflake account and least-privilege service identity.
The setup and runbooks are separated by operational responsibility:

- [Snowflake foundation and access](docs/snowflake_setup.md)
- [Source ingestion](docs/extraction.md)
- [Airflow orchestration](docs/orchestration.md)
- [Continuous integration boundaries](docs/continuous_integration.md)
- [Dashboard contract and deployment](docs/bi_consumption.md)

## Repository map

```text
src/                          Python ingestion and Snowflake loading
infrastructure/snowflake/     Warehouse objects, roles, and cost controls
dbt/nyc_building_compliance/  Transformations, tests, metadata, and exposures
airflow/dags/                 Scheduled workflow
dashboard/                    Next.js decision interface and data contract
scripts/                      Release and validation utilities
tests/                        Credential-free automated tests
docs/                         Product, architecture, runbooks, and decision records
```

## Scope and limitations

- The published snapshot contains 1,000 records from each source, not the full city population.
- The daily snapshot supports history, but only one published date currently exists; no trend is
  fabricated from a single observation.
- Legacy violations are modeled separately from newer DOB Safety Violations until a defensible
  cross-system deduplication rule is validated.
- Records without a usable building identifier remain in event facts and are excluded from
  building-level aggregates.
- The deployed dashboard is a static consumption artifact and refreshes only after a governed
  warehouse build and export.
- The corrected warehouse rebuild is pending the configured monthly Snowflake resource-monitor
  reset; the checked-in contract already excludes the discovered placeholder building.

See the [business brief](docs/business_brief.md), [official source inventory](docs/data_sources.md),
and [dimensional model](docs/data_model.md) for the complete metric and source boundaries.
