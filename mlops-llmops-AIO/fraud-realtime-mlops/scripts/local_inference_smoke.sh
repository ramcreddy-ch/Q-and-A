#!/usr/bin/env bash
set -euo pipefail

echo "[smoke] validating local fraud inference repo layout"
test -f containers/fraud-inference/requirements.txt
test -f configs/prod/fraud-endpoint.yaml
test -f docs/runbooks/fraud-endpoint-sev1.md
test -f contracts/events/card_auth_event/v2/schema.json
echo "[smoke] basic repo smoke checks passed"
