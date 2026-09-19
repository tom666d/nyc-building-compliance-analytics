# Business brief

## Problem

NYC building compliance information is split across permit, complaint, and violation datasets with different identifiers, status conventions, date fields, and source systems. A user investigating one building must reconcile those records manually, while analysts can easily publish conflicting definitions of “open,” “active,” or “resolved.”

## Proposed data product

Create a governed building-compliance analytics layer that:

1. preserves source records and ingestion metadata;
2. standardizes building identity around BIN, with BBL/address fallback flags rather than silent fuzzy matching;
3. publishes event-level facts for permits, complaints, and violations;
4. publishes a daily building snapshot for prioritization and trend reporting;
5. makes metric definitions, freshness, lineage, and quality failures visible.

## Stakeholders and decisions

| Stakeholder | Decision enabled | Primary measures |
|---|---|---|
| DOB operations manager | Prioritize inspection and case workload | open complaints, aging buckets, recent complaints |
| Property/compliance manager | Identify properties requiring action | open violations, active permits, oldest unresolved item |
| Construction program manager | Find permit lifecycle bottlenecks | approval-to-issue days, expiration exposure, status mix |
| Real-estate risk analyst | Screen a property before deeper due diligence | compliance counts, recency, data coverage flags |
| Analytics team | Reuse consistent definitions | tested facts, conformed building dimension, freshness |

## Phase 1 success criteria

- One command loads a bounded slice of real NYC Open Data into Snowflake.
- `dbt build` creates three event facts, one building dimension, and one BI-ready snapshot.
- Primary keys, accepted statuses, relationships, and critical dates are tested.
- Source freshness and ingestion timestamps are exposed.
- A reviewer can trace each dashboard measure to a documented model and source.

## Non-goals

- This is not a legal compliance determination or an official DOB replacement.
- Phase 1 does not create an opaque “risk score.” Counts and aging signals remain explainable.
- Records missing BIN are retained but excluded from building-level rollups until a defensible identity rule exists.
- Phase 1 does not claim full DOB coverage: electrical, elevator, LAA, ECB summonses, and several newer modules are separate sources.

## Initial KPI definitions

| Metric | Definition |
|---|---|
| Open complaint | latest source record where normalized complaint status is not `CLOSED` |
| Open violation | normalized legacy violation category explicitly mapped to an active category; mapping remains provisional pending domain validation |
| Active permit | permit issuance whose mapped status is active and whose expiration date has not passed; grain and mapping remain provisional |
| Complaint resolution days | calendar days from date entered to disposition date; null while unresolved |
| Permit approval-to-issue days | calendar days from approved date to issued date, only when both are present |

These definitions are hypotheses to validate with domain users, not universal facts. Live-source profiling invalidated the original permit key and the simple violation rule based only on disposition date; ADR 0004 and the source profile preserve that evidence before implementation is revised.
