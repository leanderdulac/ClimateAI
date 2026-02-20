# Database Module Outputs

output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.main.endpoint
}

output "db_port" {
  description = "Database port"
  value       = aws_db_instance.main.port
}

output "db_identifier" {
  description = "Database identifier"
  value       = aws_db_instance.main.identifier
}

output "db_arn" {
  description = "Database ARN"
  value       = aws_db_instance.main.arn
}

output "db_password_secret_arn" {
  description = "Secrets Manager ARN para senha do banco"
  value       = var.environment == "prod" ? aws_secretsmanager_secret.db_password[0].arn : null
  sensitive   = true
}
