# Schema Evolution Policy

## Goals
Protect real-time fraud serving from silent schema breakage while allowing controlled iteration.

## Compatibility rules
### Additive changes
Allowed when:
- new field is optional
- consumers ignore unknown fields safely
- replay validation confirms no semantic regression

### Breaking changes
Require:
- new contract version directory
- dual-read or translation period
- consumer migration plan
- stage replay and canary validation evidence
- explicit owner approval

## Examples
### Safe-ish change
Add optional `merchant_segment` to `card_auth_event/v2`.

### Breaking change
Rename `merchant_country` to `merchant_geo.country` without version bump.

## Production rule
If an upstream producer cannot maintain compatibility, the platform team must introduce a translation layer before the scoring path, not ask every consumer to hotfix under outage pressure.
