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

## DEBUG IMAGE ##
FROM node:14 as debug

# Make the 'app' folder the current working directory
WORKDIR /app

ARG USR
ARG PWD
ARG FIREBASE_URL

SHELL ["/bin/bash", "-c"]

# Add `/app/node_modules/.bin` to $PATH
ENV PATH /app/node_modules/.bin:$PATH

# Copy dependency files and install dependenciesInstall app dependencies by firstly copying them and installing them
COPY package*.json ./
RUN npm ci

# Only copy required files to monimize rebuild time
COPY src ./src
COPY public ./public
COPY ./*.js ./
COPY tsconfig.json .

# Download firebase config
RUN curl \
  -u $USR:$PWD $FIREBASE_URL/dev-firebase-auth-key.json \
  > /app/src/modules/config/firebaseConfig.json

ENTRYPOINT ["/bin/bash", "debug-entrypoint.sh"]
CMD ["npm", "run", "serve"]

## BUILDER IMAGE ##
FROM debug as builder

RUN npm run build

## PROD IMAGE ##
FROM nginx:1.21.1-alpine as prod

# Default NginX configuration
ENV CLIENT_MAX_BODY_SIZE="100M"
ENV NGINX_TIMEOUT="300"

# We copy the created build file to the ngnix folder
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy the nginx config template to be used in docker container
COPY deployment/default.conf.template /etc/nginx/templates/

# Add entrypoint to add env variables
COPY config-entrypoint.sh /docker-entrypoint.d/00-config-entrypoint.sh
COPY log-nginx-config.sh /docker-entrypoint.d/99-log-nginx-config.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
