import argparse
import json
import pathlib
import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-package-arn", required=True)
    parser.add_argument("--business-version", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", default="release-manifest.json")
    args = parser.parse_args()

    cfg = yaml.safe_load(pathlib.Path(args.config).read_text())
    manifest = {
        "service_name": cfg["service_name"],
        "environment": cfg["environment"],
        "model_package_arn": args.model_package_arn,
        "business_version": args.business_version,
        "threshold_config_version": cfg["threshold_config_version"],
        "feature_contract_version": cfg["feature_contract_version"],
        "rollback_target_model_package_arn": cfg["rollback_target_model_package_arn"],
        "rollback_target_endpoint_config_name": cfg["rollback_target_endpoint_config_name"],
    }
    pathlib.Path(args.output).write_text(json.dumps(manifest, indent=2))
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
