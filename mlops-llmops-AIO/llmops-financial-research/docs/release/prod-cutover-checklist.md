# Prod Cutover Checklist - Financial Research Assistant

## Before Cutover
- [ ] prompt version approved
- [ ] retrieval and rerank configs approved
- [ ] evaluation results attached
- [ ] citation presence rate acceptable
- [ ] ACL validation completed
- [ ] rollback prompt/model versions recorded

## During Canary
- [ ] p95 latency acceptable
- [ ] citation presence acceptable
- [ ] no unauthorized retrievals
- [ ] refusal behavior acceptable when evidence insufficient

## After Cutover
- [ ] 24-hour watchlist active
- [ ] stale stage or shadow resources reviewed
- [ ] release evidence attached
