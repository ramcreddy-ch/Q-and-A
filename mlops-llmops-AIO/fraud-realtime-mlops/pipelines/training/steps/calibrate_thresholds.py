def calibrate(evaluation: dict) -> dict:
    print("calibrating threshold bands using replay evaluation")
    return {
        "threshold_config_version": "fraud_thresholds_candidate_v1",
        "approve_max": 0.12,
        "review_max": 0.45,
        "decline_min": 0.45,
        "estimated_approval_rate_delta": evaluation["approval_rate_delta_estimate"],
    }
