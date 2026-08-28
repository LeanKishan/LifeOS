# Every credential lives in Secrets Manager and is injected into the task as an
# environment variable by ECS (`secrets` block in ecs.tf) — nothing sensitive is
# ever in a task definition, a tfvars file, or the git history.

resource "random_password" "db" {
  length  = 32
  special = false
}

resource "random_password" "redis" {
  length  = 32
  special = false
}

resource "random_password" "jwt" {
  length  = 48
  special = false
}

locals {
  database_url = "postgresql+psycopg://${aws_db_instance.this.username}:${random_password.db.result}@${aws_db_instance.this.address}:${aws_db_instance.this.port}/${aws_db_instance.this.db_name}"
  redis_host   = aws_elasticache_replication_group.this.primary_endpoint_address
  redis_base   = "rediss://:${random_password.redis.result}@${local.redis_host}:6379"
}

resource "aws_secretsmanager_secret" "app" {
  name                    = "${local.name}/app"
  description             = "LifeOS backend runtime secrets"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "app" {
  secret_id = aws_secretsmanager_secret.app.id
  secret_string = jsonencode({
    DATABASE_URL          = local.database_url
    REDIS_URL             = "${local.redis_base}/0"
    CELERY_BROKER_URL     = "${local.redis_base}/1"
    CELERY_RESULT_BACKEND = "${local.redis_base}/2"
    JWT_SECRET            = random_password.jwt.result
  })
}

# Created empty; set the real value with the AWS CLI or console. `ignore_changes`
# keeps Terraform from clobbering it on the next apply.
resource "aws_secretsmanager_secret" "anthropic" {
  name                    = "${local.name}/anthropic-api-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "anthropic" {
  secret_id     = aws_secretsmanager_secret.anthropic.id
  secret_string = "unset"

  lifecycle {
    ignore_changes = [secret_string]
  }
}
