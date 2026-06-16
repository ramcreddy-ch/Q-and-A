# Runbook: Entitlement Breach

## Trigger
- user sees content from unauthorized document set
- retrieval logs show chunks with disallowed ACL tags in prompt assembly

## Immediate actions
1. declare Sev1 if unauthorized content reached users
2. disable affected corpus slice or route assistant to refusal mode
3. preserve query, retrieval, and prompt assembly evidence
4. involve security/compliance and product owner

## Likely root causes
- ACL metadata missing on new ingestion batch
- retrieval filter bypass bug
- prompt assembly included unfiltered chunks

## Recovery
- restore strict ACL filtering
- reindex affected documents with correct metadata
- validate against sampled entitlement test set
