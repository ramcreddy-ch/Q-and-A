import pathlib
import yaml


def test_threshold_config_ordering():
    path = pathlib.Path(__file__).resolve().parents[2] / "configs" / "stage" / "thresholds.yaml"
    cfg = yaml.safe_load(path.read_text())
    bands = cfg["default_bands"]
    assert bands["approve_max"] < bands["review_max"]
    assert bands["review_max"] <= bands["decline_min"]
