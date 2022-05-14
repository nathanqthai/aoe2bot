<div id="top"></div>

<br />
<div align="center">
  <a href="TODO">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">AoE2Bot</h3>

  <p align="center">
    A Discord bot for AoE2 players
    <br />
    <a href="https://github.com/nathanqthai/aoe2bot"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/nathanqthai/aoe2bot">Home</a>
    ·
    <a href="https://github.com/nathanqthai/aoe2bot/issues">Report Bug</a>
    ·
    <a href="https://github.com/nathanqthai/aoe2bot/issues">Request Feature</a>
  </p>
</div>

<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
  </ol>
</details>


## About The Project

## Getting Started

### Installation
Generate the taunt files and manifest using the `./tools/taunt_scraper.py` script.

Upload these to a [DigitalOcean Space](https://cloud.digitalocean.com/spaces). The name of this space is for running the bot.

#### Local
The python bot looks for a Discord Bot Token in the `DISCORD_BOT_TOKEN` environment variable and the DigitalOcean Spaces name in the `DIGITALOCEAN_SPACES_NAME` environment variable.

#### Docker
```commandline
docker build -t aoe2dev .
docker run -e DISCORD_BOT_TOKEN=<discord bot token>} \
    -e DIGITALOCEAN_SPACES_NAME=<digitalocean space name> \
    -e DIGITALOCEAN_SPACES_KEY_ID=<digitalocean spaces access key> \
    -e DIGITALOCEAN_SPACES_SECRET=<digitalocean spaces secret key> \
    --rm aoe2dev:latest
```

### Terraform Deployment to Digital Ocean
``` bash
terraform plan -var-file="prod.tfvars"
terraform apply -out="prod.out"
```

Example `prod.tfvars`:
``` tf
# https://cloud.digitalocean.com/account/security
aoe2bot_droplet_ssh_key_name  = "<name of ssh key in DigitalOcean account>"

# https://discord.com/developers/applications/<bot client id>/oauth2/general
discord_bot_token             = "<discord bot token>"

# https://cloud.digitalocean.com/account/api/tokens
do_token                      = "<personal access token>"
do_spaces_access_id           = "<spaces key>"
do_spaces_secret_key          = "<space secret>"

# tenant, prod or dev
tenant                        = "dev"
```