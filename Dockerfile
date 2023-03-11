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

### Base image ###
FROM continuumio/miniconda3 as base
# Build the base image, including required system packages & gitlab ssh keys

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

ENV TZ=Europe/Zurich

SHELL ["/bin/bash", "-c"]
WORKDIR /app

# Update & install packages
RUN apt-get update --fix-missing && \
    apt-get install -y bash curl wget git ca-certificates openssh-client gpg tzdata && \
    apt-get clean

FROM base as build

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ape-model ./ape-model
COPY mt-model ./mt-model

RUN pip install ./ape-model && \
    pip install ./mt-model && \
    rm -rf ape-model && rm -rf mt-model

# Copy api source files & configs
COPY gunicorn.conf.py .
COPY mtc_ape_web_editor ./mtc_ape_web_editor/

CMD [ "gunicorn", "-c", "gunicorn.conf.py", "--chdir", "mtc_ape_web_editor", "-k", "uvicorn.workers.UvicornWorker", "app:app" ]

### Test image ###
FROM build as test

CMD [ "python", "-m", "unittest", "discover", "--buffer", "--verbose"]

### Debug image with additional dependencies & debug entrypoint ###
FROM build as debug

ENV DEBUG=True
EXPOSE 5678

### Production image ###
FROM build as prod

# Start server
# Only ever start one worker, parallelize with horizontally scaling containers
