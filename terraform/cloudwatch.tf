resource "aws_cloudwatch_event_rule" "every_minute" {
  name_prefix         = "every-minute-"
  schedule_expression = "rate(1 minute)"
  description         = "Runs every minute"
  is_enabled          = var.is_enabled
}

resource "aws_cloudwatch_event_target" "newegg_stock_checker" {
  rule = aws_cloudwatch_event_rule.every_minute.id
  arn  = aws_lambda_function.newegg_stock_checker.arn

  input = jsonencode({
    url      = var.url
    topicArn = aws_sns_topic.newegg_stock_checker.arn
    s3Bucket = aws_s3_bucket.newegg.id
    s3Object = "gtx3070"
  })
}

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name  = "${var.function_name}-errors"
  namespace   = "AWS/Lambda"
  metric_name = "Errors"

  # Looking over the last 60 seconds.
  period             = 60
  evaluation_periods = 1

  # Was there >= 1 error?
  comparison_operator = "GreaterThanOrEqualToThreshold"
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [aws_sns_topic.newegg_stock_checker.id]
  ok_actions    = [aws_sns_topic.newegg_stock_checker.id]

  dimensions = {
    "FunctionName" = var.function_name
  }
}
