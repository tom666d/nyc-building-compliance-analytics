# Snowflake foundation

## Status

The repeatable setup, role model, cost controls, connection validation, and local tests are implemented. Cloud provisioning has not been executed because this workspace does not contain Snowflake credentials. This distinction is intentional: repository evidence must not claim that an external environment exists when it has not been verified.

## Why Snowflake is used

Snowflake separates persistent data storage from compute. The project can retain raw source payloads in tables while starting the `NYC_DOB_WH` virtual warehouse only when ingestion, transformation, or analysis requires compute.

The first warehouse layer stores each NYC Open Data row as a `VARIANT` value plus ingestion metadata. This preserves the source payload for auditability while dbt owns parsing, type conversion, deduplication, and business logic downstream.

## Provisioned object design

| Object | Purpose |
|---|---|
| `NYC_DOB_ANALYTICS` | Project database |
| `NYC_DOB_WH` | Extra-small shared compute warehouse |
| `RAW` | Immutable source payload tables |
| `DEV` | Default dbt connection schema |
| `DEV_STAGING` | Typed and renamed source views |
| `DEV_INTERMEDIATE` | Reusable transformations |
| `DEV_MARTS` | Dimensional models and BI-facing tables |
| `NYC_DOB_LOADER` | Append and verify raw records |
| `NYC_DOB_TRANSFORMER` | Read raw data and create dbt models |
| `NYC_DOB_READER` | Read curated marts only |
| `NYC_DOB_MONTHLY_MONITOR` | One-credit monthly warehouse safety ceiling |

dbt appends a configured custom schema to its target schema. With target `DEV`, the configured schemas `staging`, `intermediate`, and `marts` therefore resolve to `DEV_STAGING`, `DEV_INTERMEDIATE`, and `DEV_MARTS`. The bootstrap creates and grants these exact schemas rather than assuming that all models land in `DEV`.

## Least-privilege boundaries

- The loader can use the warehouse and append to the three existing raw tables. It cannot create or alter dbt models.
- The transformer can select raw tables and create tables or views in the three development model schemas. It cannot insert raw source records.
- The reader can use the warehouse and select current or future tables and views in `DEV_MARTS`. It cannot see raw source tables through this role.
- All custom roles are granted into `SYSADMIN`, following Snowflake's recommended custom-role hierarchy.
- Users are not hard-coded in source control. Role assignment is a separate administrator action.

Both grants on existing objects and future grants are present. A future grant affects objects created later; it does not retroactively grant access to tables that already exist.

## Cost controls

`NYC_DOB_WH` is configured with:

- `XSMALL` warehouse size;
- automatic resume when a query needs compute;
- automatic suspension after 60 seconds of inactivity;
- initial suspended state;
- a resource monitor that notifies at 50% and 75% of one monthly credit and suspends immediately at 100%.

A credit is a Snowflake consumption unit, not a fixed dollar amount. The monitor is a guardrail, not a cost forecast. Account administrators should choose a quota appropriate to their contract and workload before treating this configuration as production-ready.

Snowflake users must enable resource-monitor notifications in their preferences, and email delivery requires a verified email address. The suspension trigger remains the enforcement control even if notification delivery is not configured.

## Setup sequence

### 1. Create or open a Snowflake account

Use a learning or employer-provided account. Record the account identifier and username. Do not place passwords in Git, documentation, screenshots, or interview materials.

### 2. Run the administrator bootstrap

In a Snowflake worksheet, run:

```text
infrastructure/snowflake/bootstrap.sql
```

The executing user must be able to assume `USERADMIN`, `SECURITYADMIN`, `SYSADMIN`, and `ACCOUNTADMIN`. `ACCOUNTADMIN` is used only for the resource monitor section and should otherwise remain restricted.

### 3. Assign project roles

Copy `infrastructure/snowflake/grant_roles.example.sql`, replace the example username, and run it with `SECURITYADMIN`. For a portfolio account, the same developer may receive all three roles and explicitly switch roles. Production automation should use separate identities and non-password authentication.

### 4. Create the local environment file

Copy `.env.example` to `.env` and fill in the local values:

```text
SNOWFLAKE_ACCOUNT=<account identifier>
SNOWFLAKE_USER=<username>
SNOWFLAKE_PASSWORD=<local secret>
```

`.env` is ignored by Git. `.env.example` contains names and safe defaults only.

### 5. Validate without changing data

Run all role checks:

```text
make snowflake-check
```

The checker connects once per workload role and reports:

- active account, user, role, warehouse, database, and schema;
- schemas visible to that role;
- raw tables visible to loader and transformer roles;
- missing expected objects;
- a final `ready` boolean.

It never prints the password. The same read-only checks are available as SQL in `infrastructure/snowflake/verify.sql`.

## Expected raw tables

Each raw table has the same append-only structure:

| Column | Type | Meaning |
|---|---|---|
| `raw_payload` | `VARIANT` | Original source row as semi-structured JSON |
| `source_dataset_id` | `VARCHAR` | Stable NYC Open Data dataset identifier |
| `source_row_hash` | `VARCHAR` | SHA-256 digest of a canonical source row |
| `load_id` | `VARCHAR` | Identifier for the load batch |
| `ingested_at` | `TIMESTAMP_TZ` | Time the project received the record, including time-zone context |

The raw layer does not rename fields or reinterpret status values. Those transformations remain reviewable in dbt models.

## Verification evidence

Local verification can prove that:

- the Python connection configuration chooses a different least-privilege role and schema for each workload;
- missing credential names produce a controlled error without exposing values;
- the dbt graph resolves to the schemas created by the bootstrap;
- the SQL, Python, and documentation are version controlled.

Only a successful check against a real Snowflake account can prove that the cloud objects and grants exist. That verification remains pending until credentials are configured locally.

## Authentication limitation

The current local learning path accepts a password from `.env`. Before automated deployment, replace long-lived password authentication with an approved non-interactive method such as Snowflake key-pair authentication and store secrets in the orchestration or continuous-integration secret manager. The repository must never contain a private key or passphrase.

## Official references

- [Snowflake access-control overview](https://docs.snowflake.com/en/user-guide/security-access-control-overview)
- [Snowflake access-control configuration](https://docs.snowflake.com/en/user-guide/security-access-control-configure)
- [Snowflake virtual warehouses](https://docs.snowflake.com/en/user-guide/warehouses-overview)
- [Snowflake warehouse cost controls](https://docs.snowflake.com/en/user-guide/cost-controlling-controls)
- [Snowflake `CREATE RESOURCE MONITOR`](https://docs.snowflake.com/en/sql-reference/sql/create-resource-monitor)
- [Snowflake Python Connector authentication](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-connect)
