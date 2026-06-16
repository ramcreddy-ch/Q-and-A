# Fraud Real-Time Reference Architecture

```text
payment/login/transfer event
  -> gateway / event router
  -> feature assembly service
  -> online feature lookups + enrichment
  -> SageMaker fraud endpoint
  -> score + reason codes
  -> decision engine
  -> approve / review / challenge / decline
  -> logging + delayed label capture
```

## Critical dependencies
- online feature freshness
- threshold configuration correctness
- endpoint autoscaling health
- model artifact availability
- decision service fallback mode

## Primary failure domains
- feature retrieval latency
- stale or defaulted online features
- endpoint config or artifact deployment issues
- threshold release mismatch
- dependency regressions in inference image
