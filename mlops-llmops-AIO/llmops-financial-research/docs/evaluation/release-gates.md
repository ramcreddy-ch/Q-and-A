# LLM Release Gates

## Required gates for regulated prod mode
- citation presence rate >= target
- groundedness pass rate >= target
- unauthorized retrieval count = 0
- refusal correctness above target
- no severe regression on latency or token budget
- critical red-team scenarios passing

## Why this matters
Prompt changes can be as risky as model changes. Treat them as first-class release artifacts.
