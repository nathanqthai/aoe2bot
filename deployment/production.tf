resource "digitalocean_droplet" "aoe2bot" {
  image         = "docker-20-04"
  name          = "${var.tenant}-aoe2bot-${var.region}"
  region        = var.region
  size          = "s-1vcpu-1gb"
  count         = 1
  ssh_keys      = [data.digitalocean_ssh_key.ssh_key.id]
  droplet_agent = true
  monitoring    = true
}

data "digitalocean_ssh_key" "ssh_key" {
  name = var.do_ssh_key_name
}

variable "do_ssh_key_name" {
  type = string
}