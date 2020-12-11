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

variable "checkers" {
  type        = map(string)
  description = "URLs for stock checkers; key is used as the scraper name and S3 object"
  default = {
    radeon6800 = "https://www.newegg.com/p/pl?d=radeon+6800&N=100007709&isdeptsrh=1&PageSize=96"
  }
}

variable "is_enabled" {
  type    = bool
  default = true
}
