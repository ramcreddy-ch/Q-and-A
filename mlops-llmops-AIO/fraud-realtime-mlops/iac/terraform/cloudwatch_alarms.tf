resource "aws_cloudwatch_metric_alarm" "endpoint_5xx_high" {
  alarm_name          = "${var.endpoint_name}-5xx-high"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 3
  metric_name         = "Invocation5XXErrors"
  namespace           = "AWS/SageMaker"
  period              = 60
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Fraud endpoint 5xx errors high"
  alarm_actions       = [var.alert_sns_topic_arn]

  dimensions = {
    EndpointName = var.endpoint_name
    VariantName  = "AllTraffic"
  }
}

resource "aws_cloudwatch_metric_alarm" "endpoint_p99_latency_high" {
  alarm_name          = "${var.endpoint_name}-p99-latency-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 5
  metric_name         = "ModelLatency"
  namespace           = "AWS/SageMaker"
  period              = 60
  extended_statistic  = "p99"
  threshold           = 250
  alarm_description   = "Fraud endpoint p99 latency high"
  alarm_actions       = [var.alert_sns_topic_arn]

  dimensions = {
    EndpointName = var.endpoint_name
    VariantName  = "AllTraffic"
  }
}

resource "aws_cloudwatch_metric_alarm" "feature_freshness_lag" {
  alarm_name          = "fraud-feature-freshness-lag-critical-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "FeatureFreshnessLagSeconds"
  namespace           = "FraudRealtime"
  period              = 60
  statistic           = "Maximum"
  threshold           = 300
  alarm_description   = "Fraud-critical feature freshness lag high"
  alarm_actions       = [var.alert_sns_topic_arn]
}
