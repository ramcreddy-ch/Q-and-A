# llmops-financial-research

Production-style LLMOps repository for a **financial research assistant** running on AWS SageMaker.

## What this repo owns
- RAG retrieval and prompt assembly logic
- SageMaker LLM endpoint deployment workflows
- reranker and generator release configuration
- evaluation datasets and quality gates
- citation, groundedness, and entitlement runbooks
- environment configs for dev, stage, and prod
- observability definitions for latency, token usage, and citation quality

## What this repo does not own
- enterprise-wide document ingestion foundations
- shared network and KMS platform baselines
- central vector database platform if managed by a separate team

## Primary production goals
- grounded answers from approved financial documents
- citations attached to every answer in regulated modes
- permission-aware retrieval
- bounded token and latency cost
- safe rollback of retriever, prompt, and model versions

## Real-time request path
```text
user query
  -> authz and entitlement check
  -> query normalization
  -> retrieval
  -> reranking
  -> prompt assembly
  -> SageMaker LLM endpoint
  -> response + citations + logs
```

## Core service levels
- p95 end-to-end latency target: <= 3.5 seconds for standard analyst queries
- citation presence rate: >= 99% for regulated answer mode
- unauthorized-document retrieval rate: 0 tolerated
- retrieval freshness to newly indexed approved docs: business-defined by corpus class

## Key directories
- `.github/workflows/`: CI, evaluation, and deploy workflows
- `configs/`: env-specific model, prompt, retrieval, and rollout configs
- `prompts/`: versioned system prompts and prompt contracts
- `retrieval/`: retrieval and citation assembly logic
- `pipelines/`: deployment and evaluation code
- `monitoring/`: alarms and dashboard definitions
- `docs/runbooks/`: incidents and on-call guides
- `eval/`: evaluation datasets and scoring rules
- `contracts/`: document metadata and retrieval ACL contracts

## Common workflows
### Run tests
```bash
make test
```

### Evaluate retrieval and citation behavior locally
```bash
make eval
```

### Validate prompt config
```bash
make validate-config ENV=stage
```

### Build release manifest
```bash
make release-manifest VERSION=research-assistant-v1.8
```
