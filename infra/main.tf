data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

locals {
  name       = "${var.project}-${var.environment}"
  account_id = data.aws_caller_identity.current.account_id
  azs        = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  # HTTPS only when we can DNS-validate a cert (domain + hosted zone).
  https_enabled = var.domain_name != "" && var.route53_zone_id != ""

  # The app's public origin — feeds CORS_ORIGINS and the HTTP->HTTPS redirect.
  origin = local.https_enabled ? "https://${var.domain_name}" : "http://${aws_lb.this.dns_name}"

  container_port = 8000
}
