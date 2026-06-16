import argparse
import pathlib
import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--canary-percent", required=True)
    args = parser.parse_args()

    cfg = yaml.safe_load(pathlib.Path(args.config).read_text())
    canary = int(args.canary_percent)
    if canary <= 0 or canary > 20:
        raise SystemExit("Initial prod LLM canary percent must be between 1 and 20")
    if not cfg.get("citation_required", False):
        raise SystemExit("Prod regulated assistant must require citations")
    if cfg.get("entitlement_mode") != "strict":
        raise SystemExit("Prod regulated assistant must use strict entitlement mode")
    print("LLMOps canary guardrails passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
