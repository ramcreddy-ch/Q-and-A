# Runbook: Online Feature Freshness Breach

## Trigger
- FeatureFreshnessLagSeconds > 300
- FeatureLookupMissRate > 2%
- MSK consumer lag grows beyond expected envelope

## Triage
1. Check consumer lag by topic and partition.
2. Check deployment history of feature consumers.
3. Verify online store write throttling or errors.
4. Determine whether fallback defaults are activating.
5. Quantify business impact on fraud decisions.

## Mitigation
- scale or restore consumers
- replay lagging partitions
- disable low-value high-write features if consumer lag is amplification-driven
- use conservative fallback thresholds if fraud-critical features are stale

## Evidence
- lag metrics
- lookup miss-rate metrics
- affected feature group names
- related deployment SHA or release run
