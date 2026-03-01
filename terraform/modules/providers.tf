# Terraform Providers para ClimateWise

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    # Docker (para desenvolvimento local)
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }

    # AWS (produção)
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }

    # Google Cloud (alternativa)
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }

    # Kubernetes
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }

    # Helm charts
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }

    # Random (para geração de senhas)
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # Backend para estado remoto (S3 + DynamoDB)
  # backend "s3" {
  #   bucket         = "climatewise-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "climatewise-terraform-locks"
  # }

  # Backend local para desenvolvimento
  backend "local" {
    path = "terraform.tfstate"
  }
}

# Provedor Docker (desenvolvimento local)
provider "docker" {
  host = "unix:///var/run/docker.sock"
}

# Provedor AWS (produção)
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Provedor Google Cloud (opcional)
# provider "google" {
#   project = var.gcp_project_id
#   region  = var.gcp_region
# }
