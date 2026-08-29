#!/bin/sh
# Container entrypoint. First argument selects the process:
#   serve   (default)  gunicorn + uvicorn workers, the API
#   web                alembic upgrade head, then serve (single-service deploys)
#   migrate            alembic upgrade head, then exit (run as a one-off task)
#   worker            celery worker
#   beat              celery beat scheduler
# Anything else is exec'd verbatim so `docker run ... sh` still works.
set -eu

cmd="${1:-serve}"
if [ "$#" -gt 0 ]; then
  shift
fi

serve() {
  exec gunicorn app.main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-2}" \
    --access-logfile - --error-logfile - \
    --forwarded-allow-ips "${FORWARDED_ALLOW_IPS:-127.0.0.1}"
}

case "$cmd" in
  serve)
    serve
    ;;
  web)
    alembic upgrade head
    serve
    ;;
  migrate)
    exec alembic upgrade head
    ;;
  worker)
    exec celery -A app.worker.celery_app.celery_app worker --loglevel=info "$@"
    ;;
  beat)
    exec celery -A app.worker.celery_app.celery_app beat --loglevel=info "$@"
    ;;
  *)
    exec "$cmd" "$@"
    ;;
esac
