# Production Cutover Checklist

## Before Cutover
- [ ] approved model package ARN recorded
- [ ] threshold config version approved
- [ ] stage replay validation attached
- [ ] shadow analysis reviewed
- [ ] rollback target tested in stage
- [ ] fraud ops staffed for cutover window
- [ ] dashboards and alerts open
- [ ] release issue updated with stop-loss thresholds

## During Canary
- [ ] verify endpoint health
- [ ] verify p95/p99 latency
- [ ] verify approval-rate delta within tolerance
- [ ] verify manual review queue impact acceptable
- [ ] verify score distribution by segment

## Before 100% Cutover
- [ ] canary hold window completed
- [ ] no unresolved Sev2+ signals
- [ ] IC / release owner signs off
- [ ] rollback owner confirms readiness

## After Cutover
- [ ] evidence bundle updated
- [ ] stale shadow resources scheduled for cleanup
- [ ] 24-hour watchlist published
