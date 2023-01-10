terraform {
  required_providers {
    digitalocean = {
      source = "digitalocean/digitalocean"
    }
    archive = {
      source = "registry.terraform.io/hashicorp/archive"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "2.16.0"
    }
  }
}