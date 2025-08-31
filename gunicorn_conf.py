import os

bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}" 
workers = 2 * (os.cpu_count() or 1) + 1
threads = 4
worker_class = "gthread"
timeout = 30
keepalive = 5
