import argparse
import json
import pathlib
import sys
import yaml

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "containers" / "fraud-inference" / "src"))
from predictor import score_request


def band(score: float, cfg: dict) -> str:
    bands = cfg["default_bands"]
    if score <= bands["approve_max"]:
        return "approve"
    if score <= bands["review_max"]:
        return "review"
    return "decline"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--thresholds", required=True)
    args = parser.parse_args()

    cfg = yaml.safe_load(pathlib.Path(args.thresholds).read_text())
    summary = {"approve": 0, "review": 0, "decline": 0}
    for line in pathlib.Path(args.fixture).read_text().strip().splitlines():
        payload = json.loads(line)
        score = score_request(payload)["risk_score"]
        summary[band(score, cfg)] += 1
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
