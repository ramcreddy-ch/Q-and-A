from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
from dataclasses import dataclass
from typing import Any

import yaml


@dataclass
class EndpointReleaseConfig:
    service_name: str
    environment: str
    region: str
    instance_type: str
    min_instances: int
    max_instances: int
    target_invocations_per_instance: int
    execution_role_arn: str
    kms_key_id: str | None
    subnet_ids: list[str]
    security_group_ids: list[str]
    tags: dict[str, str]


class SageMakerFraudDeployer:
    def __init__(self, region: str):
        import boto3

        self.region = region
        self.sm = boto3.client("sagemaker", region_name=region)
        self.aas = boto3.client("application-autoscaling", region_name=region)

    def describe_model_package(self, model_package_arn: str) -> dict[str, Any]:
        return self.sm.describe_model_package(ModelPackageName=model_package_arn)

    def resolve_primary_container(self, model_package_arn: str) -> dict[str, Any]:
        package = self.describe_model_package(model_package_arn)
        containers = package["InferenceSpecification"]["Containers"]
        if not containers:
            raise ValueError(f"No containers found in model package: {model_package_arn}")

        primary = containers[0]
        return {
            "Image": primary["Image"],
            "ModelDataUrl": primary["ModelDataUrl"],
            "Environment": {
                "SAGEMAKER_PROGRAM": "predictor.py",
                "MODEL_PACKAGE_ARN": model_package_arn,
            },
        }

    def create_model(
        self,
        model_name: str,
        model_package_arn: str,
        cfg: EndpointReleaseConfig,
    ) -> str:
        container = self.resolve_primary_container(model_package_arn)
        request = {
            "ModelName": model_name,
            "ExecutionRoleArn": cfg.execution_role_arn,
            "PrimaryContainer": container,
            "Tags": [{"Key": k, "Value": v} for k, v in cfg.tags.items()],
            "VpcConfig": {
                "Subnets": cfg.subnet_ids,
                "SecurityGroupIds": cfg.security_group_ids,
            },
        }
        if cfg.kms_key_id:
            request["EnableNetworkIsolation"] = True

        self.sm.create_model(**request)
        return model_name

    def create_endpoint_config(
        self,
        endpoint_config_name: str,
        model_name: str,
        cfg: EndpointReleaseConfig,
        route_mode: str,
        canary_percent: int,
    ) -> str:
        production_variants = [
            {
                "VariantName": "AllTraffic",
                "ModelName": model_name,
                "InstanceType": cfg.instance_type,
                "InitialInstanceCount": cfg.min_instances,
                "InitialVariantWeight": 1.0 if route_mode == "normal" else 0.0,
            }
        ]

        shadow_variant = None
        if route_mode == "shadow":
            shadow_variant = {
                "ShadowProductionVariants": [
                    {
                        "VariantName": "ShadowTraffic",
                        "ModelName": model_name,
                        "InstanceType": cfg.instance_type,
                        "InitialInstanceCount": max(1, cfg.min_instances // 2),
                        "InitialVariantWeight": 1.0,
                    }
                ]
            }
        elif route_mode == "canary":
            production_variants[0]["InitialVariantWeight"] = round((100 - canary_percent) / 100.0, 2)
            production_variants.append(
                {
                    "VariantName": "CanaryTraffic",
                    "ModelName": model_name,
                    "InstanceType": cfg.instance_type,
                    "InitialInstanceCount": max(1, cfg.min_instances // 2),
                    "InitialVariantWeight": round(canary_percent / 100.0, 2),
                }
            )

        request = {
            "EndpointConfigName": endpoint_config_name,
            "ProductionVariants": production_variants,
            "Tags": [{"Key": k, "Value": v} for k, v in cfg.tags.items()],
        }
        if cfg.kms_key_id:
            request["KmsKeyId"] = cfg.kms_key_id
        if shadow_variant:
            request.update(shadow_variant)

        self.sm.create_endpoint_config(**request)
        return endpoint_config_name

    def create_or_update_endpoint(self, endpoint_name: str, endpoint_config_name: str) -> None:
        existing = None
        try:
            existing = self.sm.describe_endpoint(EndpointName=endpoint_name)
        except self.sm.exceptions.ClientError:
            existing = None

        if existing:
            self.sm.update_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_config_name,
                RetainAllVariantProperties=True,
            )
        else:
            self.sm.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=endpoint_config_name,
                Tags=[
                    {"Key": "Service", "Value": endpoint_name},
                    {"Key": "ManagedBy", "Value": "fraud-realtime-mlops"},
                ],
            )

    def ensure_autoscaling(self, endpoint_name: str, variant_name: str, cfg: EndpointReleaseConfig) -> None:
        resource_id = f"endpoint/{endpoint_name}/variant/{variant_name}"
        self.aas.register_scalable_target(
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension="sagemaker:variant:DesiredInstanceCount",
            MinCapacity=cfg.min_instances,
            MaxCapacity=cfg.max_instances,
        )
        self.aas.put_scaling_policy(
            PolicyName=f"{endpoint_name}-{variant_name}-target-invocations",
            ServiceNamespace="sagemaker",
            ResourceId=resource_id,
            ScalableDimension="sagemaker:variant:DesiredInstanceCount",
            PolicyType="TargetTrackingScaling",
            TargetTrackingScalingPolicyConfiguration={
                "TargetValue": float(cfg.target_invocations_per_instance),
                "PredefinedMetricSpecification": {
                    "PredefinedMetricType": "SageMakerVariantInvocationsPerInstance"
                },
                "ScaleOutCooldown": 60,
                "ScaleInCooldown": 300,
            },
        )


def load_release_config(path: str) -> EndpointReleaseConfig:
    raw = yaml.safe_load(pathlib.Path(path).read_text())
    return EndpointReleaseConfig(
        service_name=raw["service_name"],
        environment=raw["environment"],
        region=raw["region"],
        instance_type=raw["instance_type"],
        min_instances=raw["min_instances"],
        max_instances=raw["max_instances"],
        target_invocations_per_instance=raw["target_invocations_per_instance"],
        execution_role_arn=raw["execution_role_arn"],
        kms_key_id=raw.get("kms_key_id"),
        subnet_ids=raw.get("subnet_ids", []),
        security_group_ids=raw.get("security_group_ids", []),
        tags=raw.get("tags", {}),
    )


def build_names(service_name: str, business_version: str) -> tuple[str, str, str]:
    stamp = dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    suffix = business_version.replace(".", "-").replace("_", "-")
    model_name = f"{service_name}-{suffix}-{stamp}"[:63]
    endpoint_config_name = f"{service_name}-cfg-{suffix}-{stamp}"[:63]
    endpoint_name = service_name[:63]
    return model_name, endpoint_config_name, endpoint_name


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--model-package-arn", required=True)
    parser.add_argument("--business-version", required=True)
    parser.add_argument("--route-mode", default="normal", choices=["normal", "shadow", "canary"])
    parser.add_argument("--canary-percent", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    cfg = load_release_config(args.config)
    model_name, endpoint_config_name, endpoint_name = build_names(cfg.service_name, args.business_version)
    release_plan = {
        "model_name": model_name,
        "endpoint_config_name": endpoint_config_name,
        "endpoint_name": endpoint_name,
        "route_mode": args.route_mode,
        "canary_percent": args.canary_percent,
        "execution_role_arn": cfg.execution_role_arn,
        "subnet_ids": cfg.subnet_ids,
        "security_group_ids": cfg.security_group_ids,
    }

    print(json.dumps(release_plan, indent=2))
    if args.dry_run:
        return 0

    deployer = SageMakerFraudDeployer(cfg.region)
    deployer.create_model(model_name, args.model_package_arn, cfg)
    deployer.create_endpoint_config(endpoint_config_name, model_name, cfg, args.route_mode, args.canary_percent)
    deployer.create_or_update_endpoint(endpoint_name, endpoint_config_name)
    deployer.ensure_autoscaling(endpoint_name, "AllTraffic", cfg)
    if args.route_mode == "canary":
        deployer.ensure_autoscaling(endpoint_name, "CanaryTraffic", cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
