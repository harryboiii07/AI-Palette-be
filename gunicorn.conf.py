"""
Gunicorn configuration for FlavorForge API production deployment
"""
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 50

# Restart workers after this many requests, with up to 50 random jitter
preload_app = True

# Logging
accesslog = "/var/log/flavorforge-api-access.log"
errorlog = "/var/log/flavorforge-api-error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "flavorforge-api"

# Server mechanics
daemon = False
pidfile = "/var/run/flavorforge-api.pid"
user = "www-data"
group = "www-data"
tmp_upload_dir = None

# SSL (uncomment if you have SSL certificates)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
