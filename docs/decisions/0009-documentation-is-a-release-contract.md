# ADR 0009: Treat published documentation as a release contract

- Status: Accepted
- Date: 2026-09-20

## Context

dbt can successfully generate a documentation site even when physical warehouse columns
have no authored descriptions. Before this decision, every published model had a model
description, but only 25 of 118 physical mart columns were documented. The exposure also
contained a placeholder URL and email address, which would weaken portfolio credibility.

Documentation can also drift in the opposite direction: YAML may retain descriptions for
columns that a SQL change has removed. A successful build does not detect either form of
metadata drift by default.

## Decision

Published marts and raw sources must satisfy a generated-artifact documentation contract:

1. every published model and physical published column has a non-empty description;
2. every raw source table and physical source column has a non-empty description;
3. documented columns and warehouse columns agree;
4. each downstream exposure has a meaningful description and owner;
5. placeholder exposure metadata is prohibited;
6. model and column descriptions are persisted to supported Snowflake relations;
7. reusable concepts use docs blocks so definitions remain consistent.

The contract is evaluated against both `manifest.json` and `catalog.json`, because the
manifest contains authored metadata while the catalog contains the actual Snowflake
structure.

## Consequences

### Benefits

- Analysts can discover definitions in dbt documentation or directly in Snowflake.
- Reviewers can trace business intelligence products to models and official sources.
- Added or removed physical columns cause a visible documentation failure.
- Portfolio evidence distinguishes authored design from a generated project skeleton.

### Costs and limitations

- Every published schema change requires a corresponding documentation change.
- A Snowflake connection is required to produce the catalog used by the full contract.
- Presence checks cannot determine whether prose is semantically correct; human review is
  still required.
- Source comments are documented in dbt but are not persisted by dbt's `persist_docs`
  configuration.

## Alternatives considered

### Rely only on `dbt docs generate`

Rejected because dbt introspection includes undocumented physical columns in the site;
generation success is not a coverage guarantee.

### Track generated documentation artifacts in Git

Rejected because artifacts contain environment-specific output, create noisy diffs, and
are reproducible from tracked definitions and the warehouse.

### Add a fabricated exposure URL until the dashboard exists

Rejected because a false link suggests completion that has not occurred. An absent optional
URL communicates the current state accurately.
