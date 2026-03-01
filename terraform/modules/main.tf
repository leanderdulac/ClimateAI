# ClimateWise - Main Infrastructure Module

# ============================================
# LOCALS
# ============================================

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Version     = "1.0.0"
  }

  environment_config = {
    dev = {
      instance_type    = "t3.micro"
      db_instance      = "db.t3.micro"
      redis_node       = "cache.t3.micro"
      multi_az         = false
      backup_retention = 7
    }
    staging = {
      instance_type    = "t3.small"
      db_instance      = "db.t3.small"
      redis_node       = "cache.t3.small"
      multi_az         = false
      backup_retention = 14
    }
    prod = {
      instance_type    = "t3.medium"
      db_instance      = "db.r5.large"
      redis_node       = "cache.r5.large"
      multi_az         = true
      backup_retention = 30
    }
  }

  current_config = local.environment_config[var.environment]
}

# ============================================
# VPC & NETWORKING
# ============================================

module "vpc" {
  source = "./networking"

  project_name  = var.project_name
  environment   = var.environment
  vpc_cidr      = var.vpc_cidr
  enable_nat    = var.enable_nat_gateway
  multi_az      = var.enable_multi_az
  common_tags   = local.common_tags
}

# ============================================
# DATABASE (PostgreSQL + Redis)
# ============================================

module "database" {
  source = "./database"

  project_name              = var.project_name
  environment               = var.environment
  vpc_id                    = module.vpc.vpc_id
  subnet_ids                = module.vpc.private_subnet_ids
  db_instance_class         = var.db_instance_class != "" ? var.db_instance_class : local.current_config.db_instance
  db_allocated_storage      = var.db_allocated_storage
  db_name                   = var.db_name
  db_username               = var.db_username
  db_backup_retention       = var.db_backup_retention_period != "" ? var.db_backup_retention_period : local.current_config.backup_retention
  enable_automatic_backups  = var.enable_db_automatic_backups
  multi_az                  = var.enable_multi_az
  common_tags               = local.common_tags
}

module "redis" {
  source = "./database/redis"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  subnet_ids          = module.vpc.private_subnet_ids
  node_type           = var.redis_node_type != "" ? var.redis_node_type : local.current_config.redis_node
  num_cache_nodes     = var.redis_num_cache_nodes
  multi_az            = var.enable_multi_az
  common_tags         = local.common_tags
}

# ============================================
# COMPUTE (Backend + Frontend)
# ============================================

module "compute" {
  source = "./compute"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  private_subnet_ids  = module.vpc.private_subnet_ids
  backend_replicas    = var.backend_replicas
  frontend_replicas   = var.frontend_replicas
  backend_cpu         = var.backend_cpu
  backend_memory      = var.backend_memory
  db_endpoint         = module.database.db_endpoint
  db_port             = module.database.db_port
  redis_endpoint      = module.redis.redis_endpoint
  redis_port          = module.redis.redis_port
  common_tags         = local.common_tags
}

# ============================================
# MONITORING (Prometheus + Grafana)
# ============================================

module "monitoring" {
  source = "./monitoring"

  count = var.enable_monitoring ? 1 : 0

  project_name            = var.project_name
  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.public_subnet_ids
  prometheus_retention    = var.prometheus_retention_days
  enable_alerting         = var.enable_alerting
  alert_email             = var.alert_email
  common_tags             = local.common_tags
}

# ============================================
# SECURITY (WAF + DDoS)
# ============================================

module "security" {
  source = "./security"

  project_name          = var.project_name
  environment           = var.environment
  enable_waf            = var.enable_waf
  enable_ddos           = var.enable_ddos_protection
  allowed_cidr_blocks   = var.allowed_cidr_blocks
  common_tags           = local.common_tags
}

# ============================================
# BACKUP & DISASTER RECOVERY
# ============================================

module "backup" {
  source = "./backup"

  count = var.enable_backups ? 1 : 0

  project_name        = var.project_name
  environment         = var.environment
  s3_bucket_name      = var.backup_s3_bucket
  db_identifier       = module.database.db_identifier
  retention_days      = local.current_config.backup_retention
  dr_enabled          = var.dr_enabled
  dr_region           = var.dr_region
  common_tags         = local.common_tags
}

# ============================================
# OUTPUTS
# ============================================

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "db_endpoint" {
  description = "Database endpoint"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.redis_endpoint
  sensitive   = true
}

output "backend_url" {
  description = "Backend URL"
  value       = module.compute.backend_url
}

output "frontend_url" {
  description = "Frontend URL"
  value       = module.compute.frontend_url
}

output "grafana_url" {
  description = "Grafana URL"
  value       = var.enable_monitoring ? module.monitoring[0].grafana_url : null
}

output "prometheus_url" {
  description = "Prometheus URL"
  value       = var.enable_monitoring ? module.monitoring[0].prometheus_url : null
}
