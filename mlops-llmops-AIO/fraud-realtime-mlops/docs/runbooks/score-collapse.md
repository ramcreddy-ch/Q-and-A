# Runbook: Score Collapse or Distribution Drift

## Trigger
- score histogram collapses toward 0 or 1
- approval/review/decline mix shifts abruptly
- score-distribution alarm fires after release

## Triage
1. compare live score distribution to prior baseline by cohort
2. inspect feature freshness and default/null-rate spikes
3. compare threshold config versions
4. validate recent model or feature release

## Mitigation
- rollback threshold config first if mismatch is clear
- revert feature retrieval change if defaults are dominating
- rollback model if unresolved and business impact rising

## Evidence
- score histogram snapshots
- feature null/default metrics
- model package and threshold versions
