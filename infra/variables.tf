variable "project" {
  type    = string
  default = "lifeos"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.20.0.0/16"
}

variable "az_count" {
  description = "Number of AZs to spread subnets across (2 is enough for an ALB)."
  type        = number
  default     = 2
}

# ── Images ─────────────────────────────────────────────────────────────────
variable "backend_image_tag" {
  description = "Tag of the backend image in ECR. The release pipeline sets this to the git SHA."
  type        = string
  default     = "latest"
}

variable "frontend_image_tag" {
  type    = string
  default = "latest"
}

# ── Sizing ─────────────────────────────────────────────────────────────────
variable "api_cpu" {
  type    = number
  default = 512
}

variable "api_memory" {
  type    = number
  default = 1024
}

variable "api_desired_count" {
  type    = number
  default = 2
}

variable "api_max_count" {
  type    = number
  default = 6
}

variable "worker_cpu" {
  type    = number
  default = 256
}

variable "worker_memory" {
  type    = number
  default = 512
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

# ── Ops ────────────────────────────────────────────────────────────────────
variable "domain_name" {
  description = "Optional public hostname, e.g. app.example.com. Requires route53_zone_id for automatic TLS."
  type        = string
  default     = ""
}

variable "route53_zone_id" {
  description = "Optional. If set (with domain_name), an ACM cert is issued + DNS-validated in this zone and HTTPS is enforced. Without it the ALB is HTTP-only on its AWS DNS name."
  type        = string
  default     = ""
}

variable "alarm_email" {
  description = "Optional. Subscribed to the CloudWatch alarm SNS topic."
  type        = string
  default     = ""
}

variable "db_deletion_protection" {
  type    = bool
  default = true
}

variable "log_retention_days" {
  type    = number
  default = 30
}

variable "github_repo" {
  description = "owner/name — the repo allowed to assume the CI deploy role via OIDC."
  type        = string
  default     = "LeanKishan/LifeOS"
}
