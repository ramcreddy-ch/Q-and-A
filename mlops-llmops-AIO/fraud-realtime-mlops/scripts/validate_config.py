import sys
import yaml

REQUIRED_FIELDS = [
    "service_name",
    "environment",
    "model_package_arn",
    "instance_type",
    "min_instances",
    "max_instances",
    "execution_role_arn",
    "subnet_ids",
    "security_group_ids",
    "threshold_config_version",
    "feature_contract_version",
    "rollback_target_model_package_arn",
]


def main(path: str) -> int:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        print(f"Missing required fields: {missing}")
        return 1

    if data["min_instances"] > data["max_instances"]:
        print("min_instances cannot exceed max_instances")
        return 1

    if not isinstance(data["subnet_ids"], list) or not data["subnet_ids"]:
        print("subnet_ids must be a non-empty list")
        return 1

    if not isinstance(data["security_group_ids"], list) or not data["security_group_ids"]:
        print("security_group_ids must be a non-empty list")
        return 1

    print(f"Config validation passed for {path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_config.py <config-path>")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
