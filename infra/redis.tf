resource "aws_elasticache_subnet_group" "this" {
  name       = local.name
  subnet_ids = aws_subnet.private[*].id
}

# Single node (no replica) — cheap, and the app treats Redis as a rebuildable
# cache + denylist, not a system of record. Encryption in transit is on, so the
# app connects with rediss:// and an auth token (see secrets.tf).
resource "aws_elasticache_replication_group" "this" {
  replication_group_id = local.name
  description          = "LifeOS cache / token denylist / celery broker"

  engine         = "redis"
  engine_version = "7.1"
  node_type      = var.redis_node_type

  num_cache_clusters         = 1
  automatic_failover_enabled = false
  multi_az_enabled           = false

  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.this.name
  security_group_ids   = [aws_security_group.database.id]
  parameter_group_name = "default.redis7"

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis.result

  snapshot_retention_limit = 1
  apply_immediately        = true

  tags = { Name = local.name }
}
