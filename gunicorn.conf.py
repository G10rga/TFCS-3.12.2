"""Gunicorn configuration for production (Ubuntu + systemd)."""

import multiprocessing

bind = "127.0.0.1:8000"
workers = max(2, multiprocessing.cpu_count())
threads = 2
timeout = 120
keepalive = 5
worker_class = "gthread"
accesslog = "-"
errorlog = "-"
capture_output = True
