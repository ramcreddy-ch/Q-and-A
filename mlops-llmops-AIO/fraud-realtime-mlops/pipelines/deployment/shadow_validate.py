import argparse
import json
import pathlib
import statistics
import sys
import yaml

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "containers" / "fraud-inference" / "src"))
from predictor import score_request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--thresholds", required=True)
    args = parser.parse_args()

    thresholds = yaml.safe_load(pathlib.Path(args.thresholds).read_text())
    scores = []
    for line in pathlib.Path(args.fixture).read_text().strip().splitlines():
        payload = json.loads(line)
        scores.append(score_request(payload)["risk_score"])

    print("=== Shadow / Replay Validation Summary ===")
    print(f"records: {len(scores)}")
    print(f"avg_score: {round(statistics.mean(scores), 4)}")
    print(f"max_score: {round(max(scores), 4)}")
    print(f"threshold_version: {thresholds['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
