output "endpoint_name" {
  value = aws_sagemaker_endpoint.fraud_endpoint.name
}

output "endpoint_execution_role_arn" {
  value = aws_iam_role.endpoint_execution.arn
}

output "endpoint_config_name" {
  value = aws_sagemaker_endpoint_configuration.fraud_endpoint_config.name
}

output "deployment_passrole_policy_arn" {
  value = aws_iam_policy.deployment_passrole.arn
}
