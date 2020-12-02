resource "aws_lambda_function" "newegg_stock_checker" {
  function_name    = var.function_name
  filename         = var.function_zipfile_name
  source_code_hash = filebase64sha256(var.function_zipfile_name)
  role             = aws_iam_role.newegg_stock_checker.arn
  handler          = "newegg.lambda_handler"
  runtime          = "python3.8"
}
