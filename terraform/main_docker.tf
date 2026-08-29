terraform {
#  required_providers {
#    docker = {
#      source  = "kreuzwerker/docker"
#      version = "~> 3.0"
#    }
#  }
}

provider "docker" {}

variable "django_secret_key" {
  description = "SECRET_KEY z GitHub"
  type        = string
  sensitive   = true
}

resource "docker_image" "sales_inventory_app" {
  name = "sales-inventory-app:latest"
  
  build {
    context    = "./src"
    dockerfile = "Dockerfile"
  }
}

resource "docker_container" "sales_inventory_web" {
  name  = "sales-inventory-management"
  image = docker_image.sales_inventory_app.name

  ports {
    internal = 8000
    external = 8080
  }

  env = [
    "SECRET_KEY=${var.django_secret_key}",
    "DEBUG=true",
    "ALLOWED_HOSTS=*",
  ]

  restart = "unless-stopped"

  # NAPRAWIONE: Tylko app katalog (nie root /)
  volumes {
    host_path      = "/home/kali/sales-and-inventory-management/data/"
    container_path = "/app"  # ZMIENIONE z "/"
  }

  depends_on = [docker_image.sales_inventory_app]
}
