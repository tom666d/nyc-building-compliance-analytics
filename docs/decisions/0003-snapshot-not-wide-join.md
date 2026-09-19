# ADR 0003: Aggregate facts before building-level combination

Status: accepted

## Decision

Aggregate each event fact independently to building grain, then join those aggregates to the building dimension.

## Rationale

Joining raw permits, complaints, and violations directly creates a fanout and inflates counts.

## Consequence

Cross-domain event correlations require purpose-built bridge models rather than ad hoc wide joins.
