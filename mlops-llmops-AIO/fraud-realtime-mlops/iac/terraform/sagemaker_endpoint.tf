resource "aws_sagemaker_model" "fraud_model" {
  name               = var.model_name
  execution_role_arn = aws_iam_role.endpoint_execution.arn

  primary_container {
    image          = var.image_uri
    model_data_url = var.model_data_url
    environment = {
      MODEL_ENVIRONMENT = var.environment
      SERVICE_NAME      = "fraud-realtime"
    }
  }

  vpc_config {
    subnets            = var.subnet_ids
    security_group_ids = var.security_group_ids
  }
}

resource "aws_sagemaker_endpoint_configuration" "fraud_endpoint_config" {
  name       = var.endpoint_config_name
  kms_key_arn = var.kms_key_id

  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.fraud_model.name
    instance_type          = var.instance_type
    initial_instance_count = var.initial_instance_count
    initial_variant_weight = 1.0
  }
}

resource "aws_sagemaker_endpoint" "fraud_endpoint" {
  name                 = var.endpoint_name
  endpoint_config_name = aws_sagemaker_endpoint_configuration.fraud_endpoint_config.name

  deployment_config {
    blue_green_update_policy {
      traffic_routing_configuration {
        type                     = "CANARY"
        wait_interval_in_seconds = 300
        canary_size {
          type  = "INSTANCE_COUNT"
          value = 1
        }
      }
      termination_wait_in_seconds = 600
      maximum_execution_timeout_in_seconds = 1800
    }
  }
}

resource "aws_appautoscaling_target" "fraud_endpoint" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "endpoint/${aws_sagemaker_endpoint.fraud_endpoint.name}/variant/AllTraffic"
  scalable_dimension = "sagemaker:variant:DesiredInstanceCount"
  service_namespace  = "sagemaker"
}

resource "aws_appautoscaling_policy" "fraud_endpoint_target_tracking" {
  name               = "${var.endpoint_name}-target-invocations"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.fraud_endpoint.resource_id
  scalable_dimension = aws_appautoscaling_target.fraud_endpoint.scalable_dimension
  service_namespace  = aws_appautoscaling_target.fraud_endpoint.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = var.target_invocations_per_instance

    predefined_metric_specification {
      predefined_metric_type = "SageMakerVariantInvocationsPerInstance"
    }

    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
