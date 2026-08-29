# infra/ — AWS deployment (Terraform)

Provisions the whole runtime on **ECS Fargate**: a VPC, an ALB, RDS Postgres,
ElastiCache Redis, an S3 bucket, ECR repos, four ECS services (`api`,
`frontend`, `worker`, `beat`), autoscaling, CloudWatch alarms, and the GitHub
OIDC role the release pipeline assumes. See `../DECISIONS.md` ADR-0023 for why
it's shaped this way.

```
            Route53 (optional)
                  │
            ┌─────▼─────┐   :443 / :80
            │    ALB    │
            └──┬─────┬──┘
     /api/*  │     │  /*
        ┌────▼──┐ ┌▼────────┐        ┌──────────┐  ┌───────────┐
        │  api  │ │ frontend│        │  worker  │  │   beat    │
        │(Fargate)│(nginx)  │        │ (celery) │  │ (celery)  │
        └──┬────┘ └─────────┘        └────┬─────┘  └─────┬─────┘
           │                              │              │
      ┌────▼───────────────────┬──────────▼──────────────▼───┐
      │  RDS Postgres 16       │      ElastiCache Redis 7     │
      └────────────────────────┴─────────────────────────────┘
```

## First-time setup

1. **Remote state** (once per account):

   ```bash
   cd infra/bootstrap
   terraform init && terraform apply
   terraform output -raw backend_hcl > ../backend.hcl
   ```

2. **The stack:**

   ```bash
   cd infra
   terraform init -backend-config=backend.hcl
   cp terraform.tfvars.example terraform.tfvars   # edit
   terraform apply
   ```

   The ECS services come up unhealthy — no images in ECR yet. That's expected.

3. **Wire CI:** put these in the GitHub repo (Settings → Secrets and variables →
   Actions):

   | name | value |
   | --- | --- |
   | `AWS_DEPLOY_ROLE_ARN` (variable) | `terraform output -raw deploy_role_arn` |
   | `AWS_REGION` (variable) | e.g. `us-east-1` |

4. **First release:** push a tag (`git tag v0.1.0 && git push --tags`) or run the
   *Release* workflow manually. It builds both images, pushes to ECR, runs the
   one-off `migrate` task, and rolls the services. They go healthy within a
   minute or two.

5. **AI assistant key** (optional): the `${name}/anthropic-api-key` secret is
   created as `unset`. To enable `/api/coach`:

   ```bash
   aws secretsmanager put-secret-value \
     --secret-id lifeos-prod/anthropic-api-key --secret-string 'sk-ant-...'
   aws ecs update-service --cluster lifeos-prod --service api --force-new-deployment
   ```

## Notes

- **`ignore_changes = [task_definition]`** on every service: the release
  pipeline is the source of truth for the running image. `terraform apply`
  manages infrastructure; it won't fight a deploy.
- **One NAT gateway**, not one per AZ — the biggest single cost here and not
  worth HA for a portfolio deploy. S3 goes over a gateway endpoint, not the NAT.
- **`high_availability = true`** flips RDS to Multi-AZ and adds a Redis replica
  with automatic failover (≈2× the DB/cache spend). Off by default.
- **`waf_enabled = true`** (default) attaches an AWS WAF to the ALB — the
  managed common + known-bad-inputs rule sets and a per-IP rate rule
  (`waf_rate_limit`, default 3000 / 5 min).
- **`terraform destroy`**: set `db_deletion_protection = false` first, or RDS
  blocks the teardown.
- **Estimated cost** at the default sizes: roughly \$70–110/month, dominated by
  the NAT gateway, the ALB, and the two always-on RDS/Redis nodes.
