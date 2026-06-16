variable "region" {
  type        = string
  description = "AWS region for the fraud serving stack"
}

variable "environment" {
  type        = string
  description = "Environment name: dev, stage, prod"
}

variable "endpoint_name" {
  type        = string
  description = "SageMaker endpoint name"
}

variable "model_name" {
  type        = string
  description = "SageMaker model resource name"
}

variable "endpoint_config_name" {
  type        = string
  description = "SageMaker endpoint configuration name"
}

variable "image_uri" {
  type        = string
  description = "Inference container image URI"
}

variable "model_data_url" {
  type        = string
  description = "S3 path to model artifacts"
}

variable "instance_type" {
  type        = string
  description = "Endpoint instance type"
}

variable "initial_instance_count" {
  type        = number
  description = "Initial instance count"
}

variable "min_capacity" {
  type        = number
  description = "Autoscaling minimum capacity"
}

variable "max_capacity" {
  type        = number
  description = "Autoscaling maximum capacity"
}

variable "target_invocations_per_instance" {
  type        = number
  description = "Target tracking value for autoscaling"
}

variable "execution_role_name" {
  type        = string
  description = "IAM role name for SageMaker endpoint execution"
}

variable "deployment_role_arn" {
  type        = string
  description = "CI/CD deployment role ARN allowed to pass execution role"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private subnets for endpoint network interfaces"
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security groups for the endpoint"
}

variable "kms_key_id" {
  type        = string
  description = "KMS key for endpoint config and model artifacts"
}

variable "model_artifact_bucket_arn" {
  type        = string
  description = "Artifact bucket ARN for model downloads"
}

variable "cloudwatch_log_group_arn" {
  type        = string
  description = "CloudWatch log group ARN for endpoint logs"
}

variable "alert_sns_topic_arn" {
  type        = string
  description = "SNS topic for alarm notifications"
}
