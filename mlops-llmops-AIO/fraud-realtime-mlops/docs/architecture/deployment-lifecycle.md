# Deployment Lifecycle Reference

## Promotion path
```text
PR merge
  -> build-release workflow
  -> stage deploy workflow
  -> replay validation
  -> shadow validation
  -> prod canary
  -> hold window
  -> 100% cutover
  -> 24h watch
```

## Key release artifacts
- immutable model package ARN
- endpoint config manifest
- threshold config version
- stage replay summary
- shadow/canary summary
- rollback target

## Decision points
- technical readiness
- business KPI readiness
- fraud ops staffing readiness
- rollback readiness

## Why this exists
Real-time fraud releases are not just code deploys. They are controlled business-risk events.
