# ADR 0002: Use BIN as canonical building identity

Status: accepted for Phase 1

## Decision

Use a validated seven-digit BIN to build the conformed building key. Retain BBL and address as attributes and future fallback candidates.

## Rationale

BIN appears across the selected DOB sources and represents a building, while BBL represents a tax lot and can map differently. Address matching without reference data introduces silent false positives.

## Consequence

Some real records remain unmatched. A coverage metric makes this tradeoff visible.
