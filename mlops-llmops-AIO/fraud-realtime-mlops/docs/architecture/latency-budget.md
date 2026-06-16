# Latency Budget

## Internal Budget Targets
- ingress / gateway: 5-10 ms
- feature assembly: 10-25 ms
- SageMaker inference: 10-30 ms
- decision service: 5-10 ms
- total internal path target: 30-75 ms

## Operating Rule
Do not spend the entire latency budget in feature enrichment and expect the model endpoint to recover it.

## Metrics to Watch
- feature assembly p95
- endpoint model latency p95
- serialization overhead
- timeout rate by caller
- approval-rate shifts during latency degradation
