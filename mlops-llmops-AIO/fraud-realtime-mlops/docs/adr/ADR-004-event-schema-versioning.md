# ADR-004: Versioned Event Contracts for Fraud Producers

- Status: Accepted
- Date: 2026-06-15

## Context
Upstream event producers evolve faster than downstream ML consumers. The fraud platform depends on stable parsing, replay, and feature materialization rules.

## Decision
All breaking changes to fraud-critical producer payloads require an explicit versioned contract path, e.g. `card_auth_event/v1` -> `card_auth_event/v2`.

## Why
- protects scoring path from silent breakage
- allows dual-read migration windows
- supports replay and incident forensics
- gives contract tests a stable target

## Consequences
- more release coordination up front
- clearer consumer expectations
- fewer emergency hotfixes during producer launches

## Alternatives Rejected
### In-place schema mutation
Rejected because it hides compatibility risk and makes replay/forensics ambiguous.
