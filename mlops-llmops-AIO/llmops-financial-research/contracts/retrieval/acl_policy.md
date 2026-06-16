# Retrieval ACL Policy

## Goal
No query may retrieve chunks from documents outside the requester's entitlements.

## Rules
- every indexed chunk must inherit document ACL metadata
- retrieval results must be filtered before reranking and prompt assembly
- missing ACL metadata is a hard failure for regulated corpora
- stage/prod promotion requires ACL validation on sampled documents

## Incident posture
If unauthorized retrieval is suspected:
- disable affected corpus slice
- revert latest retrieval/index config if relevant
- involve security/compliance immediately
