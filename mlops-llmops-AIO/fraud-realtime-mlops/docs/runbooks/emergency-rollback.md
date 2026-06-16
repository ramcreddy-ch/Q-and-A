# Runbook: Emergency Rollback

## Use This When
- canary or early full-rollout breaches stop-loss thresholds
- endpoint health regresses immediately after release
- fraud ops requests immediate return to prior champion behavior

## Rollback Order
1. freeze further changes
2. restore previous endpoint config
3. restore previous threshold config if score distribution changed
4. validate endpoint health
5. validate approval-rate proxy and manual review queue
6. record rollback completion in release issue

## Required Inputs
- current model package ARN
- rollback target package ARN
- current endpoint config name
- rollback target endpoint config name
- threshold config versions

## Verification
- p95/p99 latency back to baseline
- 5xx near normal
- no hidden queue backlog
- fraud ops confirms business behavior acceptable
