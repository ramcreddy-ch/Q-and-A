data "aws_iam_policy_document" "endpoint_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "endpoint_execution" {
  name               = var.execution_role_name
  assume_role_policy = data.aws_iam_policy_document.endpoint_assume_role.json
}

resource "aws_iam_role_policy" "endpoint_execution" {
  name = "fraud-endpoint-execution-policy"
  role = aws_iam_role.endpoint_execution.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "ReadApprovedModelArtifacts",
        Effect = "Allow",
        Action = ["s3:GetObject"],
        Resource = ["${var.model_artifact_bucket_arn}/*"]
      },
      {
        Sid    = "UseApprovedKmsKey",
        Effect = "Allow",
        Action = ["kms:Decrypt", "kms:GenerateDataKey"],
        Resource = [var.kms_key_id]
      },
      {
        Sid    = "WriteLogs",
        Effect = "Allow",
        Action = ["logs:CreateLogStream", "logs:PutLogEvents"],
        Resource = ["${var.cloudwatch_log_group_arn}:*"]
      }
    ]
  })
}

resource "aws_iam_policy" "deployment_passrole" {
  name        = "fraud-deployment-passrole-policy-${var.environment}"
  description = "Attach to the CI/CD deployment role to allow SageMaker to assume the fraud endpoint execution role"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "PassFraudEndpointExecutionRole",
        Effect = "Allow",
        Action = ["iam:PassRole"],
        Resource = [aws_iam_role.endpoint_execution.arn],
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "sagemaker.amazonaws.com"
          }
        }
      }
    ]
  })
}
