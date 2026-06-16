# One-Hour SageMaker + MLOps Crash Review

## 0-10 min: Core mental model
1. business decision path
2. data contracts and freshness
3. feature correctness online/offline
4. training reproducibility and evaluation
5. immutable promotion and rollback
6. monitoring and incident response
7. security and IAM boundaries
8. cost and capacity
9. ownership and operating model

## 10-20 min: Real-time path
Remember:
- real-time is end to end, not just endpoint
- freshness is part of correctness
- thresholds are release artifacts
- fallback mode must exist before prod

Path:
`request -> enrichment/features -> inference -> threshold/policy -> decision -> logs/labels`

## 20-30 min: Deployment + incidents
Remember:
- shadow before canary for high-risk paths
- rollback smallest safe unit first
- watch p95/p99, feature freshness, score distribution, business proxies
- runbooks and ownership are architecture

## 30-40 min: Data + feature + training
Remember:
- immutable raw data
- replayability
- point-in-time correctness
- label delay handling
- feature ownership + SLAs
- reproducible snapshots + lineage

## 40-50 min: LLMOps + leadership
Remember:
- prompt/retriever/model are all release artifacts
- citation presence != citation correctness
- ACL safety is first-class
- Principals think in roadmaps and portfolios

## 50-60 min: Answer structure
1. clarify workload + SLA
2. define decision path and failure impact
3. propose architecture
4. explain rollout/rollback
5. explain monitoring/security/cost
6. mention ownership and failure modes

## 10 lines to remember
1. SageMaker is part of the platform, not the whole platform.
2. Real-time ML is a decision path.
3. Freshness is part of correctness.
4. Thresholds and prompts are first-class release artifacts.
5. Rollback quality matters as much as rollout quality.
6. Artifact immutability is foundational.
7. Repeated incidents should become platform controls.
8. Golden paths should reduce cognitive load.
9. Staff engineers optimize for many teams.
10. Principal engineers sequence platform evolution.
