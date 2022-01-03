resource "digitalocean_spaces_bucket" "taunt_bucket" {
  name   = "${var.tenant}-taunts-${var.region}"
  region = "nyc3"
}

variable "taunts_path" {
  type    = string
  default = "../data/taunts/"
}

resource "digitalocean_spaces_bucket_object" "taunt_objects" {
  for_each = fileset(var.taunts_path, "*.ogg")

  region           = digitalocean_spaces_bucket.taunt_bucket.region
  bucket           = digitalocean_spaces_bucket.taunt_bucket.name
  key              = each.value
  source          = "${var.taunts_path}/${each.value}"
  content_type     = "audio/ogg"

  depends_on = [
    digitalocean_spaces_bucket.taunt_bucket,
  ]
}

variable "manifest" {
  type    = string
  default = "manifest.json"
}

resource "digitalocean_spaces_bucket_object" "manifest_object" {
  region           = digitalocean_spaces_bucket.taunt_bucket.region
  bucket           = digitalocean_spaces_bucket.taunt_bucket.name
  key              = var.manifest
  source          = "${var.taunts_path}/${var.manifest}"
  content_type     = "application/json"

  depends_on = [
    digitalocean_spaces_bucket.taunt_bucket,
  ]
}