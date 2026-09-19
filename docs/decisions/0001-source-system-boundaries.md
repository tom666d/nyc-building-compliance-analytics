# ADR 0001: Preserve source-system boundaries

Status: accepted

## Decision

Model DOB NOW permits, DOB complaints, and BIS violations as separate facts. Do not combine legacy and safety violations until overlap is quantified.

## Rationale

The official source warns of duplication across the violation datasets. A simple union would create impressive but unreliable totals. Preserving `source_dataset_id` supports auditability and later reconciliation.

## Consequence

Phase 1 violation coverage is explicitly incomplete, but its counts are explainable.
