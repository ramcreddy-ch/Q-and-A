ENV ?= stage
VERSION ?= research-assistant-local

.PHONY: test validate-config eval release-manifest smoke

test:
	pytest -q

validate-config:
	python scripts/validate_config.py configs/$(ENV)/assistant.yaml

eval:
	python eval/run_eval.py \
		--dataset eval/datasets/financial_qa_eval.jsonl \
		--prompt prompts/regulated_qa/v1/system_prompt.txt

release-manifest:
	python scripts/build_release_manifest.py \
		--config configs/$(ENV)/assistant.yaml \
		--version $(VERSION)

smoke:
	bash scripts/local_smoke.sh
