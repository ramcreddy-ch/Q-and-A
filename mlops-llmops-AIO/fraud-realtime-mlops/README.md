# fraud-realtime-mlops

Production MLOps repository for the **real-time fraud scoring platform** on AWS SageMaker.

## What this repo owns
- SageMaker training pipeline orchestration for fraud models
- SageMaker endpoint deployment and rollout automation
- threshold configuration release flow
- replay validation tooling
- production runbooks and release evidence templates
- environment configs for dev, stage, and prod
- monitoring definitions for fraud-serving health

## What this repo does not own
- shared VPC/network foundations
- organization-wide IAM baselines
- generic base images used across many teams
- enterprise-wide data lake ingestion outside fraud-serving needs

## Production SLOs
- endpoint availability: **99.95% or better**
- internal fraud scoring path p95: **<= 75 ms**
- fraud-critical online feature freshness: **<= 60 seconds**
- rollback readiness for endpoint config: **<= 15 minutes**

## Real-time request path
```text
payment/login/transfer event
  -> feature assembly
  -> SageMaker fraud endpoint
  -> risk score + reason codes
  -> decision service
  -> approve / step-up / decline / review
```

## Key directories
- `.github/workflows/`: CI and deploy workflows
- `configs/`: env-specific release manifests and thresholds
- `containers/fraud-inference/`: inference container code
- `pipelines/training/`: training orchestration
- `pipelines/deployment/`: rollout, canary, and rollback logic
- `docs/runbooks/`: on-call guides
- `monitoring/`: alarms and dashboard definitions
- `contracts/`: versioned event, feature, and label contracts
- `iac/terraform/`: endpoint, autoscaling, IAM, and alarm infrastructure
- `scripts/`: evidence bundle, contract validation, and local smoke helpers

## Common MLOps workflows
### Local smoke test
```bash
make smoke
```

### Validate config
```bash
make validate-config ENV=stage
```

### Run unit and contract tests
```bash
make test
```

### Build release manifest
```bash
make release-manifest MODEL_PACKAGE_ARN=arn:aws:sagemaker:... VERSION=fraud-v3.14
```

## Deployment model
1. PR CI must pass.
2. Stage deployment workflow runs.
3. Replay validation evidence is attached.
4. Shadow or canary is approved.
5. Prod deploy workflow uses immutable model package + config versions.
6. Previous stable endpoint config remains rollback target.

## Required release evidence
- model package ARN
- training pipeline execution ID
- feature bundle version
- threshold config version
- replay summary by segment
- stage latency summary
- rollback target
- watchlist for first 24 hours

## Incident quick links
- Runbook: `docs/runbooks/fraud-endpoint-sev1.md`
- Runbook: `docs/runbooks/emergency-rollback.md`
- On-call: `docs/oncall/first-60-minutes.md`
- ADR: `docs/adr/ADR-002-feature-retrieval-path.md`

## Ownership
- Platform release path: `@ml-platform/release`
- Fraud training logic: `@fraud-ds/core`
- Threshold decisions: `@fraud-ops/decisioning`
- Monitoring: `@ml-platform/observability`
