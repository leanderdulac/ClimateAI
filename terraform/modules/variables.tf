# Variáveis Terraform - ClimateWise

# ============================================
# GERAIS
# ============================================

variable "project_name" {
  description = "Nome do projeto"
  type        = string
  default     = "climatewise"
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod"
  }
}

variable "region" {
  description = "Região cloud"
  type        = string
  default     = "us-east-1"
}

variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

# ============================================
# DATABASE
# ============================================

variable "db_instance_class" {
  description = "Classe da instância do banco de dados"
  type        = string
  default     = "db.t3.micro"  # dev: db.t3.micro, prod: db.r5.large
}

variable "db_allocated_storage" {
  description = "Storage alocado em GB"
  type        = number
  default     = 20  # dev: 20, prod: 100
}

variable "db_name" {
  description = "Nome do banco de dados"
  type        = string
  default     = "climatewise"
}

variable "db_username" {
  description = "Username do banco de dados"
  type        = string
  default     = "climatewise_admin"
  sensitive   = true
}

variable "db_backup_retention_period" {
  description = "Período de retenção de backups (dias)"
  type        = number
  default     = 7  # dev: 7, prod: 30
}

variable "enable_db_automatic_backups" {
  description = "Habilitar backups automáticos"
  type        = bool
  default     = true
}

# ============================================
# REDIS
# ============================================

variable "redis_node_type" {
  description = "Tipo de nó Redis"
  type        = string
  default     = "cache.t3.micro"  # dev: cache.t3.micro, prod: cache.r5.large
}

variable "redis_num_cache_nodes" {
  description = "Número de nós Redis"
  type        = number
  default     = 1  # dev: 1, prod: 3 (cluster)
}

# ============================================
# COMPUTE
# ============================================

variable "backend_replicas" {
  description = "Número de réplicas do backend"
  type        = number
  default     = 1  # dev: 1, prod: 3+
}

variable "frontend_replicas" {
  description = "Número de réplicas do frontend"
  type        = number
  default     = 1  # dev: 1, prod: 2+
}

variable "backend_cpu" {
  description = "CPU allocation para backend"
  type        = string
  default     = "500m"  # dev: 500m, prod: 2000m
}

variable "backend_memory" {
  description = "Memory allocation para backend"
  type        = string
  default     = "512Mi"  # dev: 512Mi, prod: 4Gi
}

# ============================================
# NETWORKING
# ============================================

variable "vpc_cidr" {
  description = "CIDR block da VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "enable_nat_gateway" {
  description = "Habilitar NAT Gateway"
  type        = bool
  default     = false  # dev: false, prod: true
}

variable "enable_multi_az" {
  description = "Habilitar multi-AZ"
  type        = bool
  default     = false  # dev: false, prod: true
}

# ============================================
# MONITORING
# ============================================

variable "enable_monitoring" {
  description = "Habilitar stack de monitoramento"
  type        = bool
  default     = true
}

variable "prometheus_retention_days" {
  description = "Dias de retenção do Prometheus"
  type        = number
  default     = 15
}

variable "enable_alerting" {
  description = "Habilitar alertas"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email para alertas"
  type        = string
  default     = "alerts@climatewise.com"
}

# ============================================
# SECURITY
# ============================================

variable "enable_waf" {
  description = "Habilitar Web Application Firewall"
  type        = bool
  default     = false  # dev: false, prod: true
}

variable "enable_ddos_protection" {
  description = "Habilitar proteção DDoS"
  type        = bool
  default     = true
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks permitidos para acesso"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # Em prod, restringir!
}

# ============================================
# BACKUP & DR
# ============================================

variable "enable_backups" {
  description = "Habilitar backups"
  type        = bool
  default     = true
}

variable "backup_s3_bucket" {
  description = "S3 bucket para backups"
  type        = string
  default     = ""
}

variable "dr_enabled" {
  description = "Habilitar Disaster Recovery"
  type        = bool
  default     = false  # dev: false, prod: true
}

variable "dr_region" {
  description = "Região para Disaster Recovery"
  type        = string
  default     = "us-west-2"
}

# ============================================
# COSTS
# ============================================

variable "enable_cost_allocation_tags" {
  description = "Habilitar tags para alocação de custos"
  type        = bool
  default     = true
}

variable "budget_alert_threshold" {
  description = "Threshold para alerta de orçamento (%)"
  type        = number
  default     = 80
}
