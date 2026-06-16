# Contributing

## Goals
Every change to this repository should be:
- reviewable
- reproducible
- operationally safe
- rollback-aware

## Required Before Opening a PR
- run tests
- run config validation if config changed
- update runbook or ADR if system behavior changed materially
- include rollback notes for any prod-path change

## Review Expectations
- prod-path changes require CODEOWNER review
- threshold changes require fraud ops review
- deployment workflow changes require platform release review
- monitoring changes require observability review

## Commit Guidance
Prefer small, focused PRs. Separate these concerns when possible:
- model/training logic
- threshold changes
- deployment logic
- monitoring changes
- IAM/security changes
