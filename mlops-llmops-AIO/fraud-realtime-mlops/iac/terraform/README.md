# Terraform - Fraud Real-Time Serving Stack

This Terraform layer represents the **application-facing SageMaker serving stack** owned by the fraud-realtime-mlops repo.

## Scope
This layer manages:
- SageMaker model
- SageMaker endpoint config
- SageMaker endpoint
- autoscaling targets and policies
- endpoint execution role
- deployment role snippets used by CI/CD integration
- CloudWatch alarms for real-time serving health

## Out of Scope
This layer does not create:
- shared VPCs and subnets
- central KMS keys
- organization-wide SCPs
- global CloudTrail / Config setup

## Production usage model
- infra changes go through PR + plan review
- stage apply first
- prod apply only during approved release window
- model artifacts remain immutable and are referenced by versioned package or S3 path

## Key variables
- `environment`
- `endpoint_name`
- `model_name`
- `image_uri`
- `model_data_url`
- `execution_role_name`
- `subnet_ids`
- `security_group_ids`
- `kms_key_id`
- `alert_sns_topic_arn`

## Operational note
For real-time fraud, infra drift on endpoint config, autoscaling, and alarms can create incidents even when model quality is unchanged. Keep these resources in source control.
