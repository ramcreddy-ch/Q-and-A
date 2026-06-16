import argparse
import pathlib
import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()

    cfg = yaml.safe_load(pathlib.Path(args.config).read_text())
    print("=== Fraud Rollback Plan ===")
    print(f"service_name: {cfg['service_name']}")
    print(f"environment: {cfg['environment']}")
    print(f"rollback_target_model_package_arn: {cfg['rollback_target_model_package_arn']}")
    print(f"rollback_target_endpoint_config_name: {cfg['rollback_target_endpoint_config_name']}")
    print(f"reason: {args.reason}")
    print("action: restore previous endpoint config, restore prior threshold config if required, verify health and approval-rate proxy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
