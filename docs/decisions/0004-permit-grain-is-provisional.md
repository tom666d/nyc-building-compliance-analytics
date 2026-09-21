# ADR 0004: Treat permit grain as provisional

Status: accepted

## Context

The initial design assumed one permit record per job filing number, work permit, and sequence number. Live source profiling disproved that assumption. The same combination can contain multiple tracking numbers and work types. Even a refined combination that includes tracking number and work type can contain exact duplicate payloads, while tracking number alone can map to multiple job filings.

## Decision

Do not treat the current permit fact as production-ready. Preserve distinct source payloads, remove byte-equivalent duplicates using the source row hash, and defer business-level collapsing until the permit issuance and work-type relationship is explicitly modeled and tested.

## Consequences

- Permit counts remain provisional during the source-understanding phase.
- The current staging scaffold must be revised before the first warehouse build.
- A likely design is a permit-issuance fact plus a permit-to-work-type bridge, but this remains a hypothesis until broader profiling confirms it.
- The discovered exception becomes a documented design decision rather than hidden cleanup logic.

## Step 7 implementation outcome

The released Phase 1 model is named `fct_permit_records`, not `fct_permits`. Its declared grain is one distinct source payload keyed by the canonical row hash. This supports building-level permit activity analysis without overstating the row as a unique real-world permit. A future permit-issuance fact and work-type bridge remain deferred until their business keys are validated.
