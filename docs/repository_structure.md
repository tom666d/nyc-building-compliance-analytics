# Repository structure

This guide explains the responsibility of each tracked area. Generated outputs, credentials, caches, and downloaded source samples are intentionally excluded from version control.

## Tracked project tree

```text
.
├── README.md                         # Project entry point
├── CONTRIBUTING.md                   # Development and commit conventions
├── Makefile                          # Short, repeatable local commands
├── pyproject.toml                    # Python package, dependencies, and tool settings
├── .env.example                      # Environment-variable names without secrets
├── .gitignore                        # Local/generated paths Git must not track
├── .github/
│   ├── workflows/ci.yml              # Credential-free change validation
│   ├── workflows/snowflake-integration.yml # Protected live dbt validation
│   └── dependabot.yml                # Weekly dependency update proposals
├── src/nyc_dob_ingestion/            # Python source extraction and loading package
├── tests/                             # Automated Python tests
├── scripts/                           # Repository-level validation commands
├── infrastructure/snowflake/         # Snowflake object and permission setup
├── dbt/nyc_building_compliance/      # SQL transformations, tests, docs, and lineage
├── airflow/dags/                      # Scheduled workflow definition
├── dashboard/                         # Shareable BI application and data contract
└── docs/
    ├── business_brief.md             # Users, decisions, outcomes, and metrics
    ├── data_sources.md               # Official source inventory and limitations
    ├── source_profile.md              # Point-in-time profiling evidence
    ├── data_model.md                 # Fact grains and dimensional design
    ├── data_quality.md               # Quality contracts, audits, and evidence
    ├── lineage.md                    # Documentation coverage and end-to-end lineage
    ├── orchestration.md              # Airflow workflow, safety controls, and evidence
    ├── continuous_integration.md     # Static and protected CI boundaries
    ├── bi_consumption.md             # Dashboard metrics, evidence, and limitations
    ├── images/                        # Product screenshots used by the project README
    └── decisions/                    # Architecture Decision Records
```

## Responsibility by area

### Root files

- `README.md` tells a recruiter or contributor what the project solves and how to begin.
- `CONTRIBUTING.md` describes the expected development history and review evidence.
- `Makefile` gives memorable names to multi-step commands such as installation, tests, and dbt builds.
- `pyproject.toml` declares the Python package, supported Python version, dependencies, command entry point, and local test/lint configuration.
- `.env.example` documents required environment variables without containing credentials.
- `.gitignore` prevents credentials, caches, build output, downloaded data, and other local artifacts from entering commits.

### `src/nyc_dob_ingestion`

The Python package owns extraction from NYC Open Data and loading into the Snowflake raw layer.

- `datasets.py`: stable dataset IDs and loading configuration.
- `socrata.py`: paginated HTTP requests to the source API.
- `snowflake.py`: workload-specific connection settings and credential validation.
- `snowflake_check.py`: read-only role and object smoke checks.
- `snowflake_loader.py`: raw payload hashing and retry-safe batched Snowflake merges.
- `cli.py`: the command-line entry point that connects the components.

Keeping application code under `src/` prevents accidental imports from the repository root and makes packaging behavior more realistic.

### `tests`

Python unit tests verify deterministic behavior without requiring the live API or Snowflake. Warehouse integration tests will remain separate because they require credentials and external infrastructure.

### `infrastructure/snowflake`

Infrastructure scripts create Snowflake roles, a warehouse, database, schemas, grants, raw tables, and cost controls. `bootstrap.sql` creates the shared foundation, `grant_roles.example.sql` keeps user assignment explicit, and `verify.sql` provides read-only checks. This keeps environment setup reviewable and repeatable instead of relying only on manual console actions.

### `dbt/nyc_building_compliance`

The dbt project transforms raw records into analytical models:

```text
sources -> staging -> intermediate -> marts -> BI exposure
```

- `models/staging`: source-specific naming, typing, and basic cleanup.
- `models/intermediate`: reusable transformations that are not final user products.
- `models/marts/core`: conformed dimensions and event facts.
- `models/marts/operations`: decision-oriented building-level outputs.
- `models/marts/quality`: queryable quality scorecards and exception details.
- `macros`: reusable SQL-generating logic.
- `tests`: cross-model singular data tests that return contract violations.
- schema YAML files: descriptions, tests, relationships, and exposures.
- `packages.yml` and `package-lock.yml`: declared and resolved dbt dependencies.
- `profiles.yml`: connection settings read from environment variables.
- `models/_docs.md`: custom documentation overview and reusable business definitions.

The staging, dimensional, snapshot, and quality models have been built against the real bounded Snowflake sample. Permit grain remains explicitly source-record based until a business-level issuance key is validated.

Published models and sources are documented against both dbt's parsed manifest and the
physical Snowflake catalog. Model and column descriptions are persisted to supported
Snowflake relations, while two exposures connect the graph to the planned business
intelligence product and the operational quality monitor.

Three operations marts form the governed dashboard contract: one building per row, one borough
per row, and one platform overview row for the latest snapshot. Scoring and metric definitions
stay in dbt rather than being duplicated in the website.

### `scripts`

Repository-level checks that do not belong to the ingestion package live here.
`check_dbt_documentation.py` compares generated dbt artifacts with the physical Snowflake
catalog and fails on undocumented or stale published columns, incomplete sources, and
placeholder exposure metadata. `check_airflow_dag.py` imports the Dag without external
writes and enforces its tasks, dependencies, schedule, retry, timeout, concurrency, and
cost-safety contract. `check_ci_workflows.py` parses GitHub workflow YAML and rejects weakened
token permissions, mutable external Actions, unsafe triggers, static secret access, missing
timeouts, and missing live-integration controls. `export_dashboard_data.py` reads the consumption
marts through the least-privilege reader role and atomically refreshes the checked-in dashboard
snapshot when warehouse capacity is available.

### `airflow/dags`

The Apache Airflow Dag validates Snowflake access, ingests three official sources, checks
freshness, builds and tests dbt, generates the catalog, and enforces documentation coverage.
Orchestration code coordinates existing commands; it does not duplicate transformation
logic. Every ingestion task receives the stable Airflow run identifier, and the loader
merges on the payload hash plus that load identifier so same-run retries are idempotent.

### `.github/workflows`

GitHub Actions runs repeatable checks for proposed changes. `ci.yml` uses no secrets and checks
Python, dbt parsing, Airflow structure, dependencies, and its own workflow policy.
`snowflake-integration.yml` is a separate manual workflow behind a named environment, explicit
cost confirmation, key-pair secrets, timeout, and serialized execution. It builds dbt against
the development Snowflake target but intentionally does not ingest source data. Dependabot
proposes weekly GitHub Actions and Python dependency updates for review.

### `dashboard`

The dashboard is the platform's shareable consumption layer. It imports a bounded, validated
JSON snapshot at build time, so no Snowflake credential reaches the browser and viewing the site
does not resume a warehouse. The application contains overview, building explorer, and data-quality
views. Its validator enforces cross-view totals, allowed statuses, usable Building Identification
Numbers, and open-item arithmetic before the optimized build is accepted.

### `docs`

- Business and architecture documents are written in English for product consumers and contributors.
- Architecture Decision Records preserve important assumptions, evidence, decisions, and consequences.
- `lineage.md` records the downstream exposures, documentation contract, and verified coverage.
- `orchestration.md` records task dependencies, runtime controls, retry safety, live run evidence, and production limitations.
- `continuous_integration.md` records the trust boundary between static checks and live warehouse access, activation steps, and verified local evidence.
- `bi_consumption.md` records dashboard questions, metrics, data contract, live evidence, and limitations.

## Local and generated paths

These paths may exist locally but must not be committed:

| Path | Purpose | Why excluded |
|---|---|---|
| `.env` | Real credentials and local settings | Contains secrets |
| `.venv/` | Installed Python environment | Recreated from `pyproject.toml` |
| `.airflow-venv/` | Isolated constrained Airflow environment | Recreated by `make airflow-install` |
| `.airflow/` | Local Airflow configuration, metadata database, and logs | Environment-specific runtime state |
| `build/`, `*.egg-info/` | Python packaging output | Recreated during installation |
| `work/` | Downloaded samples and scratch analysis | Mutable and potentially large |
| `outputs/` | Local user-facing generated artifacts | Not source code |
| `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` | Tool caches | Recreated automatically |
| `dbt_packages/` | Downloaded dbt dependencies | Recreated from lock files |
| `target/`, `logs/` | dbt build output and logs | Generated by execution |
| `dashboard/node_modules/`, `dashboard/.vinext/`, `dashboard/dist/` | Website dependencies and builds | Recreated from the lock file and source |

## End-to-end ownership

```text
Official NYC Open Data
  -> src/nyc_dob_ingestion     extracts and loads auditable raw payloads
  -> Snowflake RAW             preserves source data and load metadata
  -> dbt staging               standardizes source-specific fields
  -> dbt intermediate          creates reusable transformation logic
  -> dbt marts                 publishes tested analytical facts and dimensions
  -> dbt quality               exposes health metrics and record-level exceptions
  -> dbt consumption marts     define reusable decision metrics
  -> validated JSON snapshot   separates browser access from warehouse credentials and cost
  -> dashboard                 answers stakeholder questions

tests/                         validates isolated Python behavior
infrastructure/                creates required Snowflake objects
airflow/                       schedules the task sequence
.github/workflows/             validates repository changes
docs/                          explains business meaning and design evidence
```

## Repository conventions

1. Secrets and raw exports never enter Git.
2. Every final model must declare its grain.
3. Source-specific cleanup belongs in staging, not dashboards.
4. Reusable business transformations belong in dbt, not Airflow.
5. Material design choices require an Architecture Decision Record.
6. A commit should represent one understandable change and include relevant validation.
7. Pull-request validation must not receive Snowflake credentials.
8. Hosted and live-integration evidence must not be claimed until the corresponding run exists.
