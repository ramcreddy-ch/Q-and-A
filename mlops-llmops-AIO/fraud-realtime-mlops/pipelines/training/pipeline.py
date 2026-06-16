from steps.data_readiness import check_data_readiness
from steps.evaluate import evaluate_candidate
from steps.calibrate_thresholds import calibrate
from steps.register import register_candidate


def main() -> int:
    if not check_data_readiness():
        print("training blocked: upstream data not ready")
        return 1

    training_result = {
        "model_artifact": "s3://fin-ml-artifacts/fraud-training/model.tar.gz",
        "offline_auc": 0.942,
        "precision_at_operating_point": 0.71,
    }
    evaluation = evaluate_candidate(training_result)
    threshold_bundle = calibrate(evaluation)
    register_candidate(training_result, evaluation, threshold_bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
