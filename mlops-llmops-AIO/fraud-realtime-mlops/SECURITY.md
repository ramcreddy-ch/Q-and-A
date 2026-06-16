# Security

## Reporting
Report suspected security issues through the organization's approved security channel, not public issues.

## Security Practices for This Repo
- no secrets committed to source control
- use OIDC/federated CI access, not long-lived cloud keys
- prod config changes require CODEOWNER review
- IAM or network-affecting changes require explicit security review when applicable

## High-Risk Change Types
- changes to deployment workflows
- changes to prod configs
- changes to endpoint execution or deployment role assumptions
- changes affecting entitlement checks, logging, or evidence retention
