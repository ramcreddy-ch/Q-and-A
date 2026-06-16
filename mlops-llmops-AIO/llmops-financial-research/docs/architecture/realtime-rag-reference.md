# Real-Time RAG Reference Architecture

```text
user query
  -> authz and tenant context
  -> query normalization
  -> retrieve top-k candidate chunks
  -> entitlement filter
  -> rerank
  -> prompt assembly
  -> SageMaker LLM endpoint
  -> answer with citations
  -> logs, metrics, and eval sampling
```

## Critical production dependencies
- retrieval freshness
- ACL metadata correctness
- prompt version control
- model/token latency budget
- canary and rollback safety
