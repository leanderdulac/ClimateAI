# Database Module Variables

variable "project_name" {
  description = "Nome do projeto"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, staging, prod)"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "subnet_ids" {
  description = "Subnet IDs para o banco de dados"
  type        = list(string)
}

variable "db_instance_class" {
  description = "Classe da instância do banco"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Storage alocado em GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "Nome do banco de dados"
  type        = string
  default     = "climateai"
}

variable "db_username" {
  description = "Username do banco"
  type        = string
  default     = "climateai_admin"
  sensitive   = true
}

variable "db_backup_retention" {
  description = "Período de retenção de backups (dias)"
  type        = number
  default     = 7
}

variable "enable_automatic_backups" {
  description = "Habilitar backups automáticos"
  type        = bool
  default     = true
}

variable "multi_az" {
  description = "Habilitar multi-AZ"
  type        = bool
  default     = false
}

variable "aws_region" {
  description = "AWS Region"
  type        = string
  default     = "us-east-1"
}

variable "common_tags" {
  description = "Tags comuns"
  type        = map(string)
  default     = {}
}
