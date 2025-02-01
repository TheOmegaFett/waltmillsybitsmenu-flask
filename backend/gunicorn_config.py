import eventlet
worker_class = 'eventlet'
workers = 1
bind = "0.0.0.0:5000"
worker_connections = 1000
timeout = 30
keepalive = 2
