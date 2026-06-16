# ADR-002: Caller-Side Feature Retrieval for Real-Time Fraud

- Status: Accepted
- Date: 2026-06-15

## Context
The fraud-serving path requires low-latency feature enrichment and strong separation between endpoint execution permissions and broader data access.

Two options were considered:
1. feature retrieval inside the inference container
2. feature retrieval in the caller / decision service before endpoint invocation

## Decision
We standardize on **caller-side feature retrieval** for the primary fraud endpoint.

## Why
- endpoint execution role remains tightly scoped
- feature assembly can be shared by rules engine and model path
- feature freshness and enrichment latency can be traced separately from model compute
- rollback of feature retrieval logic can happen without repackaging the model container

## Consequences
Positive:
- lower security blast radius for endpoint role
- clearer latency budgeting
- better operational separation of concerns

Negative:
- caller service becomes more complex
- contract testing between caller and endpoint becomes critical
- multiple downstream systems must agree on enriched request schema

## Alternatives Rejected
### In-container feature retrieval
Rejected as default for this domain because it expands endpoint permissions, complicates debugging, and couples model packaging too tightly to upstream feature sources.
