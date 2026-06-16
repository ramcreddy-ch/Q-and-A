#!/usr/bin/env bash
set -euo pipefail

test -f configs/prod/assistant.yaml
test -f prompts/regulated_qa/v1/system_prompt.txt
test -f docs/runbooks/citation-failure.md
echo "llmops local smoke passed"
