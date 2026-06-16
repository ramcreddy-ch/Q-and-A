# Replay Validator

This utility compares fraud scores and decision bands on replay traffic before a stage or prod rollout.

## Intended use
- validate score distribution stability
- estimate approval / review / decline movement
- compare reason-code deltas between champion and challenger
- produce evidence for stage and canary promotion

## Production note
Replay validation is a gate, not a guarantee. It must be combined with shadow and canary analysis.
