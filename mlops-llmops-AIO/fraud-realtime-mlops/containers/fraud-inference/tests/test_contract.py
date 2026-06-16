def test_feature_contract_fields_present():
    required = {"transaction_amount", "account_id", "merchant_id", "device_id", "event_ts"}
    payload = {"transaction_amount": 10.0, "account_id": "a1", "merchant_id": "m1", "device_id": "d1", "event_ts": "2026-06-15T12:00:00Z"}
    assert required.issubset(payload.keys())
