REQUIRED_FIELDS = {
    "transaction_amount",
    "account_id",
    "merchant_id",
    "device_id",
    "event_ts",
}

OPTIONAL_FIELDS = {
    "merchant_risk_score",
    "device_trust_score",
    "txn_count_15m_account",
    "country_change_flag_24h",
    "failed_login_count_1h",
}


class FeatureContractError(ValueError):
    pass


def validate_payload(payload: dict) -> None:
    missing = REQUIRED_FIELDS - set(payload.keys())
    if missing:
        raise FeatureContractError(f"Missing required fields: {sorted(missing)}")

    if payload.get("transaction_amount", 0) < 0:
        raise FeatureContractError("transaction_amount cannot be negative")
