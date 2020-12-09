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

variable "url" {
  type    = string
  default = "https://www.newegg.com/p/pl?d=gtx+3070&N=100007709&isdeptsrh=1&PageSize=96"
}

variable "is_enabled" {
  type    = bool
  default = true
}
