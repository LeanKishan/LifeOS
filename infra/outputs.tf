output "app_url" {
  description = "Public URL of the app."
  value       = local.origin
}

output "alb_dns_name" {
  value = aws_lb.this.dns_name
}

output "ecr_backend_repository" {
  value = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_repository" {
  value = aws_ecr_repository.frontend.repository_url
}

output "ecs_cluster" {
  value = aws_ecs_cluster.this.name
}

output "deploy_role_arn" {
  description = "Set as AWS_DEPLOY_ROLE_ARN in the GitHub repo for the release workflow."
  value       = aws_iam_role.deploy.arn
}

output "assets_bucket" {
  value = aws_s3_bucket.assets.bucket
}

output "db_endpoint" {
  value     = aws_db_instance.this.address
  sensitive = true
}

output "private_subnet_ids" {
  description = "Used by the release workflow's one-off migrate task."
  value       = aws_subnet.private[*].id
}

output "service_security_group_id" {
  value = aws_security_group.service.id
}
