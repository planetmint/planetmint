FROM python:3.9

RUN apt-get update \
    && pip install -U pip \
    && apt-get autoremove \
    && apt-get clean
RUN apt-get install -y vim zsh build-essential cmake openssh-client openssh-server

RUN mkdir -p /src
RUN pip install --upgrade \
    pytest~=6.2.5 \
    planetmint-driver~=0.9.0 \
    pycco \
    websocket-client~=0.47.0 \
	planetmint-cryptoconditions>=0.9.7\
	planetmint-driver>=0.9.2 \
	blns