data "aws_iam_policy_document" "lambda_trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "newegg_stock_checker" {
  name               = "newegg-stock-checker"
  assume_role_policy = data.aws_iam_policy_document.lambda_trust_policy.json
}

resource "aws_iam_role_policy_attachment" "newegg_stock_checker_base" {
  role       = aws_iam_role.newegg_stock_checker.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Allow publishing to SNS

data "aws_iam_policy_document" "publish_to_sns" {
  statement {
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.newegg_stock_checker.arn]
  }
}

resource "aws_iam_policy" "publish_to_sns" {
  name_prefix = "publish-to-sns-"
  policy      = data.aws_iam_policy_document.publish_to_sns.json
}

resource "aws_iam_policy_attachment" "publish_to_sns" {
  name       = "publish-to-sns"
  policy_arn = aws_iam_policy.publish_to_sns.arn
  roles = [
    aws_iam_role.newegg_stock_checker.id
  ]
}

# Allow S3 access

data "aws_iam_policy_document" "s3_access" {
  statement {
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.newegg.arn}/*"]
  }

  statement {
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.newegg.arn]
  }
}

resource "aws_iam_policy" "s3_access" {
  name_prefix = "s3-access-"
  policy      = data.aws_iam_policy_document.s3_access.json
}

resource "aws_iam_policy_attachment" "s3_access" {
  name       = "s3-access"
  policy_arn = aws_iam_policy.s3_access.arn
  roles = [
    aws_iam_role.newegg_stock_checker.id
  ]
}
