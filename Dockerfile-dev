ARG python_version=3.9
FROM python:${python_version}-slim
LABEL maintainer "contact@ipdb.global"

RUN apt-get update \
    && apt-get install -y git zsh curl\
    && apt-get install -y tarantool-common\
    && apt-get install -y vim build-essential cmake\
    && pip install -U pip \
    && apt-get autoremove \
    && apt-get clean
ARG backend
ARG abci_status

# When developing with Python in a docker container, we are using PYTHONBUFFERED
# to force stdin, stdout and stderr to be totally unbuffered and to capture logs/outputs
ENV PYTHONUNBUFFERED 0

ENV PLANETMINT_DATABASE_PORT 3303
ENV PLANETMINT_DATABASE_BACKEND $backend
ENV PLANETMINT_SERVER_BIND 0.0.0.0:9984
ENV PLANETMINT_WSSERVER_HOST 0.0.0.0
ENV PLANETMINT_WSSERVER_SCHEME ws

ENV PLANETMINT_WSSERVER_ADVERTISED_HOST 0.0.0.0
ENV PLANETMINT_WSSERVER_ADVERTISED_SCHEME ws

ENV PLANETMINT_TENDERMINT_PORT 26657

ENV PLANETMINT_CI_ABCI ${abci_status}

RUN mkdir -p /usr/src/app
COPY . /usr/src/app/
WORKDIR /usr/src/app
RUN pip install -e .[dev]
RUN pip install flask-cors
