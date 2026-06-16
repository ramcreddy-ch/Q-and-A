from feature_contract import validate_payload


def score_request(payload: dict) -> dict:
    validate_payload(payload)

    score = 0.02
    reason_codes = []

    amount = float(payload.get("transaction_amount", 0.0))
    merchant_risk = float(payload.get("merchant_risk_score", 0.0) or 0.0)
    device_trust = float(payload.get("device_trust_score", 1.0) or 1.0)
    velocity_15m = int(payload.get("txn_count_15m_account", 0) or 0)
    country_change = int(payload.get("country_change_flag_24h", 0) or 0)
    failed_logins = int(payload.get("failed_login_count_1h", 0) or 0)

    if amount > 500:
        score += 0.12
        reason_codes.append("HIGH_AMOUNT")
    if merchant_risk > 0.7:
        score += 0.25
        reason_codes.append("MERCHANT_RISK")
    if device_trust < 0.35:
        score += 0.20
        reason_codes.append("LOW_DEVICE_TRUST")
    if velocity_15m >= 5:
        score += 0.18
        reason_codes.append("HIGH_TXN_VELOCITY")
    if country_change == 1:
        score += 0.12
        reason_codes.append("COUNTRY_CHANGE")
    if failed_logins >= 3:
        score += 0.15
        reason_codes.append("FAILED_LOGIN_PATTERN")

    score = min(round(score, 4), 0.99)

    return {
        "risk_score": score,
        "reason_codes": reason_codes or ["BASELINE_LOW_RISK"],
        "model_version": "fraud-v3.14",
    }
