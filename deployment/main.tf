provider "digitalocean" {
  token             = var.do_token
  spaces_access_id  = var.do_spaces_access_id
  spaces_secret_key = var.do_spaces_secret_key
}

provider "archive" {}

variable "do_token" {}
variable "do_spaces_access_id" {}
variable "do_spaces_secret_key" {}

variable "region" {
  type    = string
  default = "nyc3"
}

variable "tenant" {
  type    = string
  default = "dev"
}

/* don't need this for now
resource "digitalocean_container_registry" "aoe2bot_registry" {
  name                   = "${var.tenant}-aoe2bot-registry"
  subscription_tier_slug = "starter"
}

resource "digitalocean_container_registry_docker_credentials" "aoe2bot_registry_credentials" {
  registry_name = digitalocean_container_registry.aoe2bot_registry.name
}
*/

variable "aoe2bot_droplet_ssh_key_name" {
  type = string
}

data "digitalocean_ssh_key" "aoe2bot_droplet" {
  name = var.aoe2bot_droplet_ssh_key_name
}

resource "digitalocean_droplet" "aoe2bot_droplet" {
  image         = "docker-20-04"
  name          = "${var.tenant}-aoe2bot-${var.region}"
  region        = var.region
  size          = "s-1vcpu-1gb"
  count         = 1
  ssh_keys      = [data.digitalocean_ssh_key.aoe2bot_droplet.id]
  droplet_agent = true
  monitoring    = true
  user_data     = <<EOF
  #cloud-config
  packages:

  runcmd:
    - git clone https://github.com/nathanqthai/aoe2bot.git
  EOF
}

resource "digitalocean_spaces_bucket" "aoe2bot_taunt_bucket" {
  name   = "${var.tenant}-taunts-${var.region}"
  region = "nyc3"
}

variable "taunts_path" {
  type    = string
  default = "../data/taunts/"
}

resource "digitalocean_spaces_bucket_object" "aoe2bot_taunt_objects" {
  for_each = fileset(var.taunts_path, "*.ogg")

  region       = digitalocean_spaces_bucket.aoe2bot_taunt_bucket.region
  bucket       = digitalocean_spaces_bucket.aoe2bot_taunt_bucket.name
  key          = each.value
  source       = "${var.taunts_path}/${each.value}"
  content_type = "audio/ogg"

  depends_on = [
    digitalocean_spaces_bucket.aoe2bot_taunt_bucket,
  ]
}

variable "manifest" {
  type    = string
  default = "manifest.json"
}

resource "digitalocean_spaces_bucket_object" "aoe2bot_manifest_object" {
  region       = digitalocean_spaces_bucket.aoe2bot_taunt_bucket.region
  bucket       = digitalocean_spaces_bucket.aoe2bot_taunt_bucket.name
  key          = var.manifest
  source       = "${var.taunts_path}/${var.manifest}"
  content_type = "application/json"

  depends_on = [
    digitalocean_spaces_bucket.aoe2bot_taunt_bucket,
  ]
}