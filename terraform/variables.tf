variable "region" {
  type    = string
  default = "us-east-1"
}

variable "function_name" {
  type    = string
  default = "newegg-stock-checker"
}

variable "function_zipfile_name" {
  type    = string
  default = "newegg.zip"
}
