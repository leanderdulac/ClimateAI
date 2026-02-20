# Database Module - PostgreSQL para ClimateAI

resource "random_password" "db_password" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Secrets Manager para senha do banco
resource "aws_secretsmanager_secret" "db_password" {
  count = var.environment == "prod" ? 1 : 0

  name        = "${var.project_name}/${var.environment}/db-password"
  description = "Database password for ${var.project_name} ${var.environment}"
  tags        = var.common_tags
}

resource "aws_secretsmanager_secret_version" "db_password" {
  count = var.environment == "prod" ? 1 : 0

  secret_id     = aws_secretsmanager_secret.db_password[0].id
  secret_string = jsonencode({ password = random_password.db_password.result })
}

# RDS PostgreSQL
resource "aws_db_instance" "main" {
  identifier = "${var.project_name}-db-${var.environment}"

  # Engine
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  max_allocated_storage = var.environment == "prod" ? 500 : null
  storage_type         = "gp3"
  storage_encrypted    = true

  # Database
  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result
  port     = 5432

  # Network
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false

  # High Availability
  multi_az               = var.multi_az
  availability_zone      = var.multi_az ? null : "${var.aws_region}a"

  # Backups
  backup_retention_period     = var.db_backup_retention
  backup_window              = "03:00-04:00"
  maintenance_window         = "Mon:04:00-Mon:05:00"
  auto_minor_version_upgrade = true

  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql"]
  performance_insights_enabled    = var.environment == "prod" ? true : false
  monitoring_interval             = var.environment == "prod" ? 60 : 0

  # Deletion protection
  deletion_protection = var.environment == "prod" ? true : false
  skip_final_snapshot = var.environment == "prod" ? false : true
  final_snapshot_identifier = var.environment == "prod" ? "${var.project_name}-final-snapshot" : null

  tags = var.common_tags
}

# Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-${var.environment}"
  subnet_ids = var.subnet_ids

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-db-subnet-${var.environment}"
  })
}

# Security Group
resource "aws_security_group" "db" {
  name        = "${var.project_name}-db-sg-${var.environment}"
  description = "Security group for ${var.project_name} database"
  vpc_id      = var.vpc_id

  tags = merge(var.common_tags, {
    Name = "${var.project_name}-db-sg-${var.environment}"
  })
}

# Database outputs
output "db_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "db_port" {
  value = aws_db_instance.main.port
}

output "db_identifier" {
  value = aws_db_instance.main.identifier
}

output "db_password_secret_arn" {
  value     = var.environment == "prod" ? aws_secretsmanager_secret.db_password[0].arn : null
  sensitive = true
}
