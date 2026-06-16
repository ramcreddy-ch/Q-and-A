ENV ?= stage
MODEL_PACKAGE_ARN ?= arn:aws:sagemaker:us-east-1:123456789012:model-package/fraud-example
VERSION ?= fraud-local

.PHONY: test smoke validate-config validate-contract release-manifest deploy-plan rollback-plan replay-sim

test:
	pytest -q

smoke:
	bash scripts/local_inference_smoke.sh

validate-config:
	python scripts/validate_config.py configs/$(ENV)/fraud-endpoint.yaml

release-manifest:
	python scripts/build_release_manifest.py \
		--model-package-arn $(MODEL_PACKAGE_ARN) \
		--business-version $(VERSION) \
		--config configs/$(ENV)/fraud-endpoint.yaml

deploy-plan:
	python pipelines/deployment/deploy.py \
		--env $(ENV) \
		--config configs/$(ENV)/fraud-endpoint.yaml \
		--model-package-arn $(MODEL_PACKAGE_ARN) \
		--business-version $(VERSION)

rollback-plan:
	python pipelines/deployment/rollback.py \
		--config configs/$(ENV)/fraud-endpoint.yaml \
		--reason "manual-local-check"

replay-sim:
	python services/threshold-simulator/simulate_thresholds.py \
		--fixture tests/fixtures/sample_requests.jsonl \
		--thresholds configs/$(ENV)/thresholds.yaml
