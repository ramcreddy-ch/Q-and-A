import argparse
import pathlib
import subprocess
import sys

import yaml

sys.path.append(str(pathlib.Path(__file__).resolve().parent))
from sagemaker_deployer import load_release_config, build_names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--model-package-arn", required=True)
    parser.add_argument("--business-version", required=True)
    parser.add_argument("--route-mode", default=None)
    parser.add_argument("--canary-percent", default="0")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(pathlib.Path(args.config).read_text())
    route_mode = args.route_mode or config.get("route_mode", "normal")
    cfg = load_release_config(args.config)
    model_name, endpoint_config_name, endpoint_name = build_names(cfg.service_name, args.business_version)

    print("=== Fraud Deploy Plan ===")
    print(f"environment: {args.env}")
    print(f"service_name: {config['service_name']}")
    print(f"business_version: {args.business_version}")
    print(f"model_package_arn: {args.model_package_arn}")
    print(f"instance_type: {config['instance_type']}")
    print(f"capacity_range: {config['min_instances']}..{config['max_instances']}")
    print(f"route_mode: {route_mode}")
    print(f"canary_percent: {args.canary_percent}")
    print(f"model_name: {model_name}")
    print(f"endpoint_config_name: {endpoint_config_name}")
    print(f"endpoint_name: {endpoint_name}")
    print(f"rollback_target: {config['rollback_target_model_package_arn']}")
    print("action: create/update model -> endpoint config -> endpoint -> scaling policy")

    if not args.apply:
        print("mode: dry-run plan only")
        return 0

    deployer_script = pathlib.Path(__file__).resolve().parent / "sagemaker_deployer.py"
    command = [
        sys.executable,
        str(deployer_script),
        "--config",
        args.config,
        "--model-package-arn",
        args.model_package_arn,
        "--business-version",
        args.business_version,
        "--route-mode",
        route_mode,
        "--canary-percent",
        str(args.canary_percent),
    ]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
