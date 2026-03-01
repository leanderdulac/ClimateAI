# ClimateWise - Produção Environment

# ============================================
# PROVIDERS
# ============================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "climatewise-terraform-state-prod"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "climatewise-terraform-locks"
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
  default = "prod"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "dr_region" {
  type    = string
  default = "us-west-2"
}

# ============================================
# LOCALS
# ============================================

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Compliance  = "SOC2,HIPAA"
  }

  # Configurações específicas para produção
  prod_config = {
    db_instance_class     = "db.r5.large"
    db_storage            = 100
    redis_node_type       = "cache.r5.large"
    redis_nodes           = 3
    backend_replicas      = 3
    frontend_replicas     = 2
    multi_az              = true
    backup_retention      = 30
    enable_waf            = true
    enable_nat_gateway    = true
  }
}

# ============================================
# VPC & NETWORKING
# ============================================

module "vpc" {
  source = "../../modules/networking"

  project_name      = var.project_name
  environment       = var.environment
  vpc_cidr          = "10.0.0.0/16"
  enable_nat_gateway = true
  multi_az          = true
  common_tags       = local.common_tags
}

# ============================================
# DATABASE (RDS PostgreSQL - Multi AZ)
# ============================================

module "database" {
  source = "../../modules/database"

  project_name         = var.project_name
  environment          = var.environment
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.private_subnet_ids
  db_instance_class    = local.prod_config.db_instance_class
  db_allocated_storage = local.prod_config.db_storage
  db_name              = "climatewise"
  db_username          = "climatewise_admin"
  db_backup_retention  = local.prod_config.backup_retention
  multi_az             = true
  aws_region           = var.aws_region
  common_tags          = local.common_tags
}

# ============================================
# REDIS (ElastiCache Cluster)
# ============================================

module "redis" {
  source = "../../modules/database/redis"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  node_type           = local.prod_config.redis_node_type
  num_cache_nodes     = local.prod_config.redis_nodes
  multi_az            = true
  common_tags         = local.common_tags
}

# ============================================
# KUBERNETES (EKS)
# ============================================

module "eks" {
  source = "../../modules/compute/eks"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  backend_replicas    = local.prod_config.backend_replicas
  frontend_replicas   = local.prod_config.frontend_replicas
  db_endpoint         = module.database.db_endpoint
  redis_endpoint      = module.redis.redis_endpoint
  common_tags         = local.common_tags
}

# ============================================
# MONITORING (Prometheus + Grafana)
# ============================================

module "monitoring" {
  source = "../../modules/monitoring"

  project_name         = var.project_name
  environment          = var.environment
  vpc_id               = module.vpc.vpc_id
  subnet_ids           = module.vpc.public_subnet_ids
  prometheus_retention = 30
  enable_alerting      = true
  alert_email          = "alerts@climatewise.com"
  common_tags          = local.common_tags
}

# ============================================
# SECURITY (WAF + Shield)
# ============================================

module "security" {
  source = "../../modules/security"

  project_name        = var.project_name
  environment         = var.environment
  enable_waf          = true
  enable_ddos         = true
  allowed_cidr_blocks = ["0.0.0.0/0"]  # Restringir em produção!
  common_tags         = local.common_tags
}

# ============================================
# DISASTER RECOVERY (Cross-Region Backup)
# ============================================

module "dr_backup" {
  source = "../../modules/backup"

  project_name   = var.project_name
  environment    = var.environment
  dr_enabled     = true
  dr_region      = var.dr_region
  s3_bucket_name = "climatewise-backups-${var.environment}"
  retention_days = 90
  common_tags    = local.common_tags
}

# ============================================
# OUTPUTS
# ============================================

output "vpc_id" {
  value = module.vpc.vpc_id
}

output "db_endpoint" {
  value     = module.database.db_endpoint
  sensitive = true
}

output "redis_endpoint" {
  value     = module.redis.redis_endpoint
  sensitive = true
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "grafana_url" {
  value = module.monitoring.grafana_url
}

output "prometheus_url" {
  value = module.monitoring.prometheus_url
}

output "dr_bucket_arn" {
  value = module.dr_backup.backup_bucket_arn
}
