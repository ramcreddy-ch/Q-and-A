#!/usr/bin/env bash
set -euo pipefail

ENVIRONMENT=${1:-prod}
VERSION=${2:-unknown}
OUT="deployment-evidence-${ENVIRONMENT}-${VERSION}.md"

cat > "$OUT" <<EOF
# Deployment Evidence

- environment: ${ENVIRONMENT}
- business version: ${VERSION}
- generated at: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Required Attachments
- model package ARN
- stage replay report
- shadow or canary summary
- threshold config version
- rollback target
- approver identities

## First 24 Hour Watchlist
- endpoint p95/p99 latency
- 5xx rate
- feature freshness lag
- approval-rate proxy
- manual review queue depth
EOF

echo "wrote ${OUT}"
