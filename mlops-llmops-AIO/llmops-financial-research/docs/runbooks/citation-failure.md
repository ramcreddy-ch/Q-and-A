# Runbook: Citation Failure

## Trigger
- citation presence rate drops
- answers return without required citations
- stale or irrelevant citations appear after retrieval or prompt release

## Triage
1. check latest prompt version
2. check retrieval and rerank config changes
3. validate corpus freshness and index refresh
4. compare stage and prod prompt assembly behavior

## Mitigation
- revert prompt version
- reduce top-k or restore last known-good retriever config
- force citations-required refusal mode if grounding uncertain

## Exit criteria
- citation presence rate returns to baseline
- sampled answers show correct document linkage
