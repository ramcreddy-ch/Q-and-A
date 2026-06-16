# Architecture Review Template - Fraud Real-Time Workload

## 1. Business context
- use case:
- business owner:
- decision impact if wrong:
- decision impact if slow:
- peak traffic assumptions:

## 2. Real-time path
- request path summary:
- latency budget by stage:
- fallback mode:
- threshold / decision coupling:

## 3. Data and feature dependencies
- producer contracts involved:
- freshness-critical features:
- replayability status:
- default / missing semantics:

## 4. Serving and rollout
- endpoint pattern:
- rollout strategy:
- stop-loss metrics:
- rollback unit:
- rollback tested in stage?:

## 5. Monitoring and incident readiness
- key dashboards:
- critical alarms:
- runbooks linked:
- incident owner:

## 6. Security and compliance
- execution role:
- KMS key:
- VPC/network assumptions:
- approval requirements:

## 7. Review outcome
- approved / stage-only / redesign required:
- conditions:
- owners:
- due dates:
