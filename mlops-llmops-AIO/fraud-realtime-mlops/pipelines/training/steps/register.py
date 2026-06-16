def register_candidate(training_result: dict, evaluation: dict, threshold_bundle: dict) -> None:
    print("registering model candidate with lineage and threshold calibration metadata")
    print({
        "model_artifact": training_result["model_artifact"],
        "evaluation": evaluation,
        "threshold_bundle": threshold_bundle,
    })
