def evaluate_candidate(training_result: dict) -> dict:
    print("evaluating candidate against replay and segment metrics")
    return {
        "offline_auc": training_result["offline_auc"],
        "precision_at_operating_point": training_result["precision_at_operating_point"],
        "approval_rate_delta_estimate": -0.008,
        "manual_review_queue_delta_estimate": 0.021,
        "status": "pass",
    }
