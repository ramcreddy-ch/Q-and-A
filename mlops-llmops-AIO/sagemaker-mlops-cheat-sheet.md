# SageMaker + MLOps Condensed Cheat Sheet

## Design order
1. business decision path
2. data contracts and freshness
3. feature correctness
4. training and evaluation
5. promotion and rollback
6. monitoring and incident handling
7. security and auditability
8. cost and capacity
9. ownership and operating model

## Serving mode cheat sheet
- real-time: synchronous fraud/risk
- async: heavy delayed tasks
- batch: bulk scoring
- serverless: sporadic low-criticality
- multi-model: many small low-QPS models
- custom/EKS: only for real managed-path gaps

## Real-time red flags
- no fallback mode
- no rollback target
- no feature freshness visibility
- thresholds outside governance
- no replay/shadow evidence
- endpoint role too broad
- business KPIs not monitored

## Fraud metrics
- p95/p99 latency
- 4xx/5xx
- feature freshness lag
- default rate
- score distribution
- approval-rate proxy
- review queue depth

## LLM metrics
- p95 latency
- citation presence
- citation correctness samples
- groundedness pass rate
- unauthorized retrieval count
- token cost per flow

## Rollout checklist
- immutable artifact?
- config versioned?
- threshold/prompt versioned?
- validated in stage?
- shadow/canary evidence?
- stop-loss metrics?
- rollback rehearsed?
- runbooks linked?

## Security checklist
- separate training / endpoint / deploy roles
- tight passrole
- KMS + private networking
- secrets manager, not git
- bucket + endpoint policies
- audit trail for releases

## Data + feature checklist
- raw immutable?
- contracts versioned?
- replayable?
- point-in-time correct?
- owner defined?
- freshness SLA defined?
- default semantics explicit?

## LLMOps checklist
- prompt versioned?
- retrieval config versioned?
- citation required?
- refusal behavior defined?
- ACL enforced?
- groundedness eval exists?
- red-team suite exists?

## Staff answer formula
business context -> architecture choice -> tradeoffs -> rollout/rollback -> monitoring -> security/cost -> ownership -> failure modes

## Principal answer formula
Staff formula + platform strategy + exception path + portfolio impact + roadmap + team topology + governance + measurable outcomes

## Final reminder
Do not answer with AWS services only.
Answer with:
- how it works
- how it fails
- how it is observed
- how it is rolled back
- who owns it
- why the tradeoff is worth it
