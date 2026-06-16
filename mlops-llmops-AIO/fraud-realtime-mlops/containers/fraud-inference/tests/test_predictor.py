import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from predictor import score_request


def test_score_request_high_risk():
    payload = {
        "transaction_amount": 1200.0,
        "account_id": "a1",
        "merchant_id": "m9",
        "device_id": "d9",
        "event_ts": "2026-06-15T12:00:00Z",
        "merchant_risk_score": 0.9,
        "device_trust_score": 0.2,
        "txn_count_15m_account": 8,
        "country_change_flag_24h": 1,
        "failed_login_count_1h": 4,
    }
    result = score_request(payload)
    assert result["risk_score"] > 0.7
    assert "MERCHANT_RISK" in result["reason_codes"]


def test_score_request_low_risk():
    payload = {
        "transaction_amount": 20.0,
        "account_id": "a1",
        "merchant_id": "m1",
        "device_id": "d1",
        "event_ts": "2026-06-15T12:00:00Z",
        "merchant_risk_score": 0.1,
        "device_trust_score": 0.95,
        "txn_count_15m_account": 0,
        "country_change_flag_24h": 0,
        "failed_login_count_1h": 0,
    }
    result = score_request(payload)
    assert result["risk_score"] < 0.2
