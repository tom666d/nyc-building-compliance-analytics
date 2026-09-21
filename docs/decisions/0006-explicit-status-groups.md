# ADR 0006: Use explicit status groups and preserve unknowns

Status: accepted

## Context

The three sources use different lifecycle fields. Complaints expose `ACTIVE` and `CLOSED`; approved-permit records expose `PERMIT ISSUED` and `SIGNED-OFF`; legacy violations encode status in category strings. Full violation profiling found several active and dismissed variants, including work-without-permit, unserved Environmental Control Board, and hazardous categories.

Inferring an open violation from a null disposition date is unsafe. In the bounded sample, one resolved violation had no disposition date, while the category still identified it as resolved.

## Decision

Create governed analytical groups in each event fact:

- complaints: `ACTIVE`, `RESOLVED`, or `UNKNOWN`;
- permit records: `ISSUED`, `SIGNED_OFF`, or `UNKNOWN`;
- violations: `ACTIVE`, `RESOLVED`, `DISMISSED`, or `UNKNOWN`, based on explicit category labels.

Only the explicit active group contributes to open counts. Unknown values remain in the fact, set an `is_status_unmapped` flag, and appear as an unmapped count in the daily snapshot.

## Consequences

- Dashboard counts remain explainable and do not silently reinterpret new source values.
- New or ambiguous categories do not break ingestion or disappear.
- Domain review can focus on visible unknown counts.
- The mapping is still an analytical definition, not an official legal compliance determination.
