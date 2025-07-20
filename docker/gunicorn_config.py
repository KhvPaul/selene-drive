from config import settings


workers = 1
worker_class = "main.CustomUvicornWorker"
# worker_class = "uvicorn.workers.UvicornWorker"
timeout = 60
keepalive = 5
loglevel = settings.LOG_LEVEL.lower()
accesslog = "-"
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s [%(t)s] "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'

max_requests = 1000
bind = f"{settings.SERVER_HOST}:{settings.SERVER_PORT}"  # noqa: E231
disable_redirect_access_to_syslog = True
