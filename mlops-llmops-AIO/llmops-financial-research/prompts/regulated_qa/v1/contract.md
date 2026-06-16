# Prompt Contract - regulated_qa_v1

## Requirements
- answers must be grounded in retrieved context
- citations required for material factual statements
- if no sufficient evidence, answer must refuse or state insufficiency
- no speculation about non-provided documents
- no cross-tenant or unauthorized content leakage

## Metrics
- citation presence rate
- groundedness pass rate
- unsupported-claim rate
- refusal correctness rate
