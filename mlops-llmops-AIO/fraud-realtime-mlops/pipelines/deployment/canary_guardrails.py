import argparse
import pathlib
import yaml


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--thresholds", required=True)
    parser.add_argument("--canary-percent", required=True)
    args = parser.parse_args()

    cfg = yaml.safe_load(pathlib.Path(args.thresholds).read_text())
    canary = int(args.canary_percent)
    if canary <= 0 or canary > 25:
        raise SystemExit("canary_percent must be between 1 and 25 for first prod shift")

    if not cfg.get("simulation_required", False):
        raise SystemExit("threshold config must require simulation for prod rollout")

    print("Canary guardrail validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
