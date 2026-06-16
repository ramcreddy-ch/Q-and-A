import sys
import yaml

REQUIRED = [
    "service_name",
    "environment",
    "base_model_id",
    "endpoint_name",
    "prompt_version",
    "retrieval_top_k",
    "rerank_top_k",
    "max_input_tokens",
    "max_output_tokens",
    "citation_required",
    "entitlement_mode",
]


def main(path: str) -> int:
    data = yaml.safe_load(open(path, "r", encoding="utf-8"))
    missing = [k for k in REQUIRED if k not in data]
    if missing:
        print(f"Missing required keys: {missing}")
        return 1
    if data["rerank_top_k"] > data["retrieval_top_k"]:
        print("rerank_top_k cannot exceed retrieval_top_k")
        return 1
    if data["max_output_tokens"] > data["max_input_tokens"]:
        print("max_output_tokens should not exceed max_input_tokens in this policy")
        return 1
    print(f"Config validation passed for {path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_config.py <config>")
        raise SystemExit(1)
    raise SystemExit(main(sys.argv[1]))
