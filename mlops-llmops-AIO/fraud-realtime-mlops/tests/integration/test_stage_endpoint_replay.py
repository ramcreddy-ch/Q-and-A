import json
import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[2] / "containers" / "fraud-inference" / "src"))

from predictor import score_request


def test_replay_fixture_scores_span_low_and_high_risk():
    fixture = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "sample_requests.jsonl"
    scores = []
    for line in fixture.read_text().strip().splitlines():
        payload = json.loads(line)
        scores.append(score_request(payload)["risk_score"])
    assert min(scores) < 0.2
    assert max(scores) > 0.7
