#!/usr/bin/env bash
# Register fresh task-definition revisions pinned to the images just pushed, run
# `alembic upgrade head` as a one-off Fargate task, then point every service at
# its new revision and wait for the rollout to stabilize.
set -euo pipefail

CLUSTER="${CLUSTER:-lifeos-prod}"
: "${BACKEND_IMAGE:?}" "${FRONTEND_IMAGE:?}"

# describe the current revision of $1, swap in image $2, register, echo new ARN
new_taskdef() {
  local family="$1" image="$2"
  aws ecs describe-task-definition --task-definition "$family" \
    --query taskDefinition >/tmp/td.json
  jq --arg IMG "$image" '
    .containerDefinitions |= map(.image = $IMG)
    | del(.taskDefinitionArn, .revision, .status, .requiresAttributes,
          .compatibilities, .registeredAt, .registeredBy)
  ' /tmp/td.json >/tmp/td-new.json
  aws ecs register-task-definition --cli-input-json file:///tmp/td-new.json \
    --query taskDefinition.taskDefinitionArn --output text
}

API_TD=$(new_taskdef lifeos-prod-api "$BACKEND_IMAGE")
WORKER_TD=$(new_taskdef lifeos-prod-worker "$BACKEND_IMAGE")
BEAT_TD=$(new_taskdef lifeos-prod-beat "$BACKEND_IMAGE")
FRONTEND_TD=$(new_taskdef lifeos-prod-frontend "$FRONTEND_IMAGE")
echo "registered: $API_TD / $WORKER_TD / $BEAT_TD / $FRONTEND_TD"

# ---- migrations: one-off task on the new API image ----
NETCFG=$(aws ecs describe-services --cluster "$CLUSTER" --services api \
  --query 'services[0].networkConfiguration' --output json)

TASK_ARN=$(aws ecs run-task --cluster "$CLUSTER" --launch-type FARGATE \
  --task-definition "$API_TD" --started-by "release-${GITHUB_SHA:-manual}" \
  --network-configuration "$NETCFG" \
  --overrides '{"containerOverrides":[{"name":"api","command":["migrate"]}]}' \
  --query 'tasks[0].taskArn' --output text)
echo "migrate task: $TASK_ARN"

aws ecs wait tasks-stopped --cluster "$CLUSTER" --tasks "$TASK_ARN"
EXIT=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" \
  --query 'tasks[0].containers[0].exitCode' --output text)
if [ "$EXIT" != "0" ]; then
  echo "::error::migration task exited with $EXIT"
  aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" \
    --query 'tasks[0].stoppedReason' --output text || true
  exit 1
fi

# ---- roll the services ----
aws ecs update-service --cluster "$CLUSTER" --service api      --task-definition "$API_TD"      >/dev/null
aws ecs update-service --cluster "$CLUSTER" --service worker   --task-definition "$WORKER_TD"   >/dev/null
aws ecs update-service --cluster "$CLUSTER" --service beat     --task-definition "$BEAT_TD"     >/dev/null
aws ecs update-service --cluster "$CLUSTER" --service frontend --task-definition "$FRONTEND_TD" >/dev/null

echo "waiting for services to stabilize..."
aws ecs wait services-stable --cluster "$CLUSTER" --services api frontend worker beat
echo "deploy complete: ${GITHUB_SHA:-manual}"
