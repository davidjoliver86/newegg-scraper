resource "aws_s3_bucket" "newegg" {
  bucket_prefix = "io-github-davidjoliver86-newegg-"
  acl           = "private"
}
