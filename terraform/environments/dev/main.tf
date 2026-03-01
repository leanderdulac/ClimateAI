# ClimateWise - Desenvolvimento Environment

# ============================================
# PROVIDERS
# ============================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

# ============================================
# VARIABLES
# ============================================

variable "project_name" {
  type    = string
  default = "climatewise"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

# ============================================
# LOCALS
# ============================================

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# ============================================
# VPC (Docker local para dev)
# ============================================

# Para desenvolvimento local, usamos Docker
# Em cloud, descomente o módulo VPC

# module "vpc" {
#   source = "../../modules/networking"
#   ...
# }

# ============================================
# DATABASE (Docker para dev)
# ============================================

resource "docker_network" "climatewise" {
  name = "${var.project_name}-${var.environment}"
}

resource "docker_volume" "postgres_data" {
  name = "${var.project_name}-postgres-data"
}

resource "docker_volume" "redis_data" {
  name = "${var.project_name}-redis-data"
}

resource "docker_container" "postgres" {
  name  = "${var.project_name}-postgres-${var.environment}"
  image = "postgres:15-alpine"

  networks_advanced {
    name = docker_network.climatewise.name
  }

  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }

  env = [
    "POSTGRES_DB=climatewise",
    "POSTGRES_USER=climatewise_admin",
    "POSTGRES_PASSWORD=climatewise_dev_123",
    "PGDATA=/var/lib/postgresql/data/pgdata"
  ]

  ports {
    internal = 5432
    external = 5432
  }

  restart = "unless-stopped"

  healthcheck {
    test         = ["CMD-SHELL", "pg_isready -U climatewise_admin -d climatewise"]
    interval     = "10s"
    timeout      = "5s"
    retries      = 5
    start_period = "30s"
  }
}

resource "docker_container" "redis" {
  name  = "${var.project_name}-redis-${var.environment}"
  image = "redis:7-alpine"

  networks_advanced {
    name = docker_network.climatewise.name
  }

  volumes {
    volume_name    = docker_volume.redis_data.name
    container_path = "/data"
  }

  ports {
    internal = 6379
    external = 6379
  }

  command = ["redis-server", "--appendonly", "yes"]

  restart = "unless-stopped"

  healthcheck {
    test         = ["CMD", "redis-cli", "ping"]
    interval     = "10s"
    timeout      = "5s"
    retries      = 5
  }
}

# ============================================
# MLFLOW (Docker para dev)
# ============================================

resource "docker_volume" "mlflow_data" {
  name = "${var.project_name}-mlflow-data"
}

resource "docker_container" "mlflow" {
  name  = "${var.project_name}-mlflow-${var.environment}"
  image = "ghcr.io/mlflow/mlflow:latest"

  networks_advanced {
    name = docker_network.climatewise.name
  }

  volumes {
    volume_name    = docker_volume.mlflow_data.name
    container_path = "/mlflow"
  }

  ports {
    internal = 5000
    external = 5000
  }

  command = [
    "mlflow",
    "server",
    "--host", "0.0.0.0",
    "--port", "5000",
    "--backend-store-uri", "sqlite:////mlflow/mlflow.db",
    "--default-artifact-root", "file:///mlflow/artifacts"
  ]

  restart = "unless-stopped"
}

# ============================================
# HASHICORP VAULT (Docker para dev)
# ============================================

resource "docker_volume" "vault_data" {
  name = "${var.project_name}-vault-data"
}

resource "docker_container" "vault" {
  name  = "${var.project_name}-vault-${var.environment}"
  image = "hashicorp/vault:latest"

  networks_advanced {
    name = docker_network.climatewise.name
  }

  volumes {
    volume_name    = docker_volume.vault_data.name
    container_path = "/vault/data"
  }

  ports {
    internal = 8200
    external = 8200
  }

  env = [
    "VAULT_DEV_ROOT_TOKEN_ID=my-secret-token",
    "VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200"
  ]

  cap_add = ["IPC_LOCK"]

  restart = "unless-stopped"
}

# ============================================
# OUTPUTS
# ============================================

output "postgres_connection" {
  value = "postgresql://climatewise_admin:climatewise_dev_123@localhost:5432/climatewise"
}

output "redis_connection" {
  value = "redis://localhost:6379"
}

output "mlflow_url" {
  value = "http://localhost:5000"
}

output "vault_url" {
  value = "http://localhost:8200"
}

output "vault_token" {
  value     = "my-secret-token"
  sensitive = true
}
