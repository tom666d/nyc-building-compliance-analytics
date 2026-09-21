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
├── .github/workflows/ci.yml          # Automated validation on GitHub
├── src/nyc_dob_ingestion/            # Python source extraction and loading package
├── tests/                             # Automated Python tests
├── infrastructure/snowflake/         # Snowflake object and permission setup
├── dbt/nyc_building_compliance/      # SQL transformations, tests, docs, and lineage
├── airflow/dags/                      # Scheduled workflow definition
└── docs/
    ├── business_brief.md             # Users, decisions, outcomes, and metrics
    ├── data_sources.md               # Official source inventory and limitations
    ├── source_profile.md              # Point-in-time profiling evidence
    ├── data_model.md                 # Fact grains and dimensional design
    ├── data_quality.md               # Quality contracts, audits, and evidence
    ├── decisions/                    # Architecture Decision Records
    └── learning/                     # Traditional Chinese learning notes
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
- `snowflake_loader.py`: raw payload hashing and Snowflake inserts.
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

The staging, dimensional, snapshot, and quality models have been built against the real bounded Snowflake sample. Permit grain remains explicitly source-record based until a business-level issuance key is validated.

### `airflow/dags`

The Apache Airflow Directed Acyclic Graph defines the intended task order: ingest source data, check freshness, then build and test the dbt project. Orchestration code coordinates existing tasks; it should not duplicate transformation logic.

### `.github/workflows`

GitHub Actions runs repeatable checks for proposed changes. Static validation can run without Snowflake; the integration job requires protected credentials.

### `docs`

- Business and architecture documents are written in English for the portfolio audience.
- `docs/learning` is written in Traditional Chinese for step-by-step study.
- Architecture Decision Records preserve important assumptions, evidence, decisions, and consequences.

## Local and generated paths

These paths may exist locally but must not be committed:

| Path | Purpose | Why excluded |
|---|---|---|
| `.env` | Real credentials and local settings | Contains secrets |
| `.venv/` | Installed Python environment | Recreated from `pyproject.toml` |
| `build/`, `*.egg-info/` | Python packaging output | Recreated during installation |
| `work/` | Downloaded samples and scratch analysis | Mutable and potentially large |
| `outputs/` | Local user-facing generated artifacts | Not source code |
| `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` | Tool caches | Recreated automatically |
| `dbt_packages/` | Downloaded dbt dependencies | Recreated from lock files |
| `target/`, `logs/` | dbt build output and logs | Generated by execution |

## End-to-end ownership

```text
Official NYC Open Data
  -> src/nyc_dob_ingestion     extracts and loads auditable raw payloads
  -> Snowflake RAW             preserves source data and load metadata
  -> dbt staging               standardizes source-specific fields
  -> dbt intermediate          creates reusable transformation logic
  -> dbt marts                 publishes tested analytical facts and dimensions
  -> dbt quality               exposes health metrics and record-level exceptions
  -> BI consumption            answers stakeholder questions

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
