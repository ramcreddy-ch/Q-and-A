# Runbook: Sev1 Fraud Endpoint Outage

## Trigger
Use this runbook when:
- SageMaker endpoint is `Failed`, `OutOfService`, or returning sustained 5xx
- p99 latency breaches hard SLA with material timeout impact
- decision service cannot obtain scores for a significant portion of live traffic

## First 5 Minutes
1. Acknowledge alert and page incident commander.
2. Freeze non-essential deployments.
3. Confirm blast radius:
   - all traffic or one region/AZ?
   - only one model family or all endpoint variants?
4. Check if fallback rules-only mode is active.
5. Open incident notes and record current endpoint config ARN.

## First 15 Minutes
1. Inspect endpoint events.
2. Inspect CloudWatch logs for startup/runtime failures.
3. Determine whether issue began after:
   - deployment
   - autoscaling change
   - feature service issue
   - upstream IAM/KMS/network change
4. Compare stage/prod differences if stage remains healthy.
5. Decide rollback vs. forward-fix.

## Decision Rules
- Roll back immediately if outage began right after rollout.
- Use conservative rules-only fallback if endpoint unavailable and approved by fraud ops.
- If feature layer is broken but endpoint is healthy, fix or bypass feature dependency first.
- If one region is degraded, consider DR or traffic shift per routing policy.

## Mitigation Actions
- Restore previous stable endpoint config.
- Restore prior autoscaling settings if scale policy was changed.
- Disable optional enrichments via feature flags.
- Increase provisioned capacity if saturation caused failure.

## Exit Criteria
- 5xx and timeout rate return to normal.
- fraud ops confirms expected decision flow restored.
- backlog or queue depth is not still growing.

## Evidence to Preserve
- endpoint events
- container logs
- deployment workflow run URL
- current and previous endpoint config ARNs
- related config versions and model package ARN
