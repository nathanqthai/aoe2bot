provider "digitalocean" {
  token             = var.do_token
  spaces_access_id  = var.do_spaces_access_id
  spaces_secret_key = var.do_spaces_secret_key
}

provider "archive" {}

variable "do_token" {}
variable "do_spaces_access_id" {}
variable "do_spaces_secret_key" {}