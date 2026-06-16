import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "containers" / "fraud-inference" / "src"))
from predictor import score_request


def main() -> int:
    fixture = pathlib.Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "sample_requests.jsonl"
    for line in fixture.read_text().strip().splitlines():
        payload = json.loads(line)
        print(score_request(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
