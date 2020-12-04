resource "aws_lambda_function" "newegg_stock_checker" {
  function_name    = var.function_name
  filename         = var.function_zipfile_name
  source_code_hash = filebase64sha256(var.function_zipfile_name)
  role             = aws_iam_role.newegg_stock_checker.arn
  handler          = "newegg.lambda_handler"
  runtime          = "python3.8"
}

resource "aws_lambda_permission" "newegg_stock_checker_every_minute" {
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.newegg_stock_checker.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.every_minute.arn
}
