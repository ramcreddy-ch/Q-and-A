from __future__ import annotations

from sagemaker.estimator import Estimator
from sagemaker.inputs import TrainingInput
from sagemaker.model_metrics import MetricsSource, ModelMetrics
from sagemaker.processing import Processor, ProcessingInput, ProcessingOutput
from sagemaker.session import Session
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.parameters import ParameterInteger, ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.workflow.model_step import RegisterModel


DEFAULT_IMAGE = "123456789012.dkr.ecr.us-east-1.amazonaws.com/fraud-training:latest"


def build_pipeline(
    session: Session,
    role_arn: str,
    bucket: str,
    pipeline_name: str = "fraud-realtime-training-pipeline",
) -> Pipeline:
    training_snapshot_uri = ParameterString(
        name="TrainingSnapshotUri",
        default_value=f"s3://{bucket}/ml/training_sets/fraud/latest/",
    )
    model_package_group = ParameterString(
        name="ModelPackageGroupName",
        default_value="fraud-realtime-tabular",
    )
    training_instance_count = ParameterInteger(name="TrainingInstanceCount", default_value=1)

    readiness_processor = Processor(
        role=role_arn,
        image_uri=DEFAULT_IMAGE,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        sagemaker_session=session,
    )

    readiness_report = PropertyFile(name="ReadinessReport", output_name="readiness", path="readiness.json")
    readiness_step = ProcessingStep(
        name="DataReadinessCheck",
        processor=readiness_processor,
        inputs=[
            ProcessingInput(source=training_snapshot_uri, destination="/opt/ml/processing/input")
        ],
        outputs=[
            ProcessingOutput(output_name="readiness", source="/opt/ml/processing/output")
        ],
        code="pipelines/training/steps/data_readiness.py",
        property_files=[readiness_report],
    )

    estimator = Estimator(
        image_uri=DEFAULT_IMAGE,
        role=role_arn,
        instance_count=training_instance_count,
        instance_type="ml.c7i.4xlarge",
        output_path=f"s3://{bucket}/model-artifacts/fraud/",
        sagemaker_session=session,
        base_job_name="fraud-realtime-train",
        hyperparameters={
            "objective": "binary:logistic",
            "max_depth": 8,
            "eta": 0.08,
            "eval_metric": "aucpr",
        },
        environment={
            "TRAINING_SNAPSHOT_URI": training_snapshot_uri,
            "FEATURE_BUNDLE_VERSION": "fraud_features_2026_06_14_01",
            "LABEL_DEFINITION_VERSION": "fraud_label_policy_v5",
        },
    )

    train_step = TrainingStep(
        name="TrainFraudCandidate",
        estimator=estimator,
        inputs={
            "train": TrainingInput(
                s3_data=training_snapshot_uri,
                content_type="text/csv",
            )
        },
    )

    evaluation_processor = Processor(
        role=role_arn,
        image_uri=DEFAULT_IMAGE,
        instance_count=1,
        instance_type="ml.m5.xlarge",
        sagemaker_session=session,
    )
    evaluation_report = PropertyFile(name="EvaluationReport", output_name="evaluation", path="evaluation.json")
    evaluate_step = ProcessingStep(
        name="EvaluateFraudCandidate",
        processor=evaluation_processor,
        inputs=[
            ProcessingInput(
                source=train_step.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model",
            ),
            ProcessingInput(source=training_snapshot_uri, destination="/opt/ml/processing/eval-data"),
        ],
        outputs=[
            ProcessingOutput(output_name="evaluation", source="/opt/ml/processing/output")
        ],
        code="pipelines/training/steps/evaluate.py",
        property_files=[evaluation_report],
    )

    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri=evaluate_step.properties.ProcessingOutputConfig.Outputs[0].S3Output.S3Uri,
            content_type="application/json",
        )
    )

    register_step = RegisterModel(
        name="RegisterFraudCandidate",
        estimator=estimator,
        model_data=train_step.properties.ModelArtifacts.S3ModelArtifacts,
        content_types=["application/json"],
        response_types=["application/json"],
        inference_instances=["ml.c7i.2xlarge", "ml.c7i.4xlarge"],
        transform_instances=["ml.m5.2xlarge"],
        model_package_group_name=model_package_group,
        approval_status="PendingManualApproval",
        model_metrics=model_metrics,
        customer_metadata_properties={
            "feature_bundle_version": "fraud_features_2026_06_14_01",
            "label_definition_version": "fraud_label_policy_v5",
            "threshold_calibration_required": "true",
        },
    )

    quality_gate = ConditionStep(
        name="FraudQualityGate",
        conditions=[
            ConditionGreaterThanOrEqualTo(
                left=evaluate_step.properties.PropertyFiles["EvaluationReport"]["offline_auc"],
                right=0.93,
            )
        ],
        if_steps=[register_step],
        else_steps=[],
    )

    return Pipeline(
        name=pipeline_name,
        parameters=[training_snapshot_uri, model_package_group, training_instance_count],
        steps=[readiness_step, train_step, evaluate_step, quality_gate],
        sagemaker_session=session,
    )
