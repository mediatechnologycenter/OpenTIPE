# Copyright 2022 ETH Zurich, Media Technology Center

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py

# Bind & deployment

bind = '0.0.0.0:5000'
reload = True

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
