# Snowflake deployment evidence

## Verification event

The project foundation was provisioned and verified in a real Snowflake trial account through Snowsight on 2026-09-20. Account-specific identifiers and user credentials are deliberately excluded from version control.

## Executed artifacts

The cloud run used the same version-controlled artifacts available to reviewers:

- `infrastructure/snowflake/bootstrap.sql` for roles, grants, compute, schemas, raw tables, and cost controls;
- `infrastructure/snowflake/grant_roles.example.sql` as the pattern for assigning project roles to the development user;
- `infrastructure/snowflake/verify.sql` for read-only role and object checks.

The worksheet copy of the verification SQL was named `step_05_snowflake_verification.sql` so the cloud activity can be identified without embedding private account details in the repository.

## Observed results

| Check | Observed result |
|---|---|
| Bootstrap execution | All 46 statements succeeded |
| Custom roles | Loader, transformer, and reader roles created and assigned |
| Database | Project database exists and is accessible through the intended roles |
| Schemas | `RAW`, `DEV`, `DEV_STAGING`, `DEV_INTERMEDIATE`, and `DEV_MARTS` exist |
| Raw tables | Three expected tables exist in `RAW` |
| Role verification | Loader, transformer, and reader read-only checks succeeded |
| Warehouse size | Extra-small |
| Warehouse lifecycle | Auto-resume enabled and auto-suspend set to 60 seconds |
| Resource monitor | One-credit monthly project monitor attached |
| Curated marts | Zero tables, as expected before the first dbt build |
| Local service authentication | Loader, transformer, and reader key-pair connections returned ready |
| Bounded raw load | 1,000 real rows in each of the three raw tables |
| Staging build | Three views and 13 tests completed successfully |

## What this evidence does and does not prove

This run proves that the SQL is executable in Snowflake, the expected cloud objects exist, the role hierarchy can be used, and the cost controls are attached. It is stronger than a local syntax check alone.

It does not yet prove that:

- all 6.6 million source rows can be loaded within the selected cost and runtime constraints;
- dimensional marts build successfully under their final grain definitions;
- scheduled orchestration and continuous integration can authenticate in their remote environments.

Those outcomes belong to later milestones and will receive separate evidence. This distinction prevents the portfolio from presenting scaffolded or planned work as completed production behavior.
