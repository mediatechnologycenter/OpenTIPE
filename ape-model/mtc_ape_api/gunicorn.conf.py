# https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

# Bind & deployment
bind = '0.0.0.0:5000'
reload = False

# Connections
workers = 1
threads = 4
backlog = 64
timeout = 300

# Logging
# log to stdout
errorlog = '-'
loglevel = 'info'
accesslog = '-'
