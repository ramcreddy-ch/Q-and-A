# Replay and Backfill Contract Rules

## Why replayability matters
For real-time fraud, replay is required for:
- incident investigation
- candidate model validation
- threshold calibration
- feature logic debugging
- schema migration confidence

## Required properties of replay-safe contracts
- stable event ID
- event timestamp as seen by producer
- no lossy transformations in raw zone
- explicit versioned schema
- documented null/default semantics

## Backfill rule
Historical reconstruction must use event-time semantics, not processing-time shortcuts.

## Dangerous anti-patterns
- dedup logic only in online path, not replay path
- implicit default values undocumented in contract
- enum expansion without replaying prior traffic to validate downstream behavior
