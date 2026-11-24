terraform {
  required_version = ">= 1.5"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

variable "django_secret_key" {
  description = "Django SECRET_KEY."
  type        = string
  sensitive   = true
}

variable "external_port" {
  description = "Port on this machine the app is published on."
  type        = number
  default     = 8080
}

variable "allowed_hosts" {
  description = "Comma separated host names the app answers to."
  type        = string
  default     = "localhost,127.0.0.1"
}

resource "docker_image" "sales_inventory_app" {
  name = "sales-inventory-app:latest"

  build {
    context    = "${path.module}/../.."
    dockerfile = "Dockerfile"
  }
}

# The database lives on a named volume, so recreating the container keeps it.
resource "docker_volume" "data" {
  name = "sales-inventory-data"
}

resource "docker_container" "sales_inventory_web" {
  name    = "sales-inventory-management"
  image   = docker_image.sales_inventory_app.image_id
  restart = "unless-stopped"

  ports {
    internal = 8000
    external = var.external_port
    ip       = "127.0.0.1"
  }

  # Local environment over plain HTTP, so no HTTPS redirect. DEBUG stays off.
  env = [
    "SECRET_KEY=${var.django_secret_key}",
    "ALLOWED_HOSTS=${var.allowed_hosts}",
    "SECURE_SSL_REDIRECT=False",
  ]

  volumes {
    volume_name    = docker_volume.data.name
    container_path = "/app/data"
  }
}
