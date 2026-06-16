# Data Contracts for Real-Time Fraud MLOps

This directory contains the **producer/consumer contracts** that protect the real-time fraud decision path.

## Why these contracts exist
In production, the fraud platform breaks more often from:
- payload schema drift
- silent field renames
- null-rate explosions
- enum expansion without consumer support
- replay/backfill incompatibility
than from model code itself.

## Contract classes in this repo
- `events/`: source event contracts from gateways, apps, and upstream systems
- `features/`: enriched feature payload contract sent to fraud scoring
- `labels/`: delayed fraud-outcome contract used for training and evaluation
- `policies/`: governance rules for schema evolution, versioning, compatibility, and replay

## Operating rule
No breaking schema change should reach stage or prod without:
- contract review
- replay validation
- compatibility decision
- version update if required
- consumer migration plan
