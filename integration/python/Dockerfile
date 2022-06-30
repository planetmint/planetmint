FROM python:3.9

RUN apt-get update \
    && pip install -U pip \
    && apt-get autoremove \
    && apt-get clean
RUN apt-get install -y vim 
RUN apt-get update
RUN apt-get install -y build-essential cmake openssh-client openssh-server
RUN apt-get install -y zsh

RUN mkdir -p /src
RUN pip install --upgrade meson ninja
RUN pip install --upgrade \
    pytest~=6.2.5 \
    planetmint-driver~=0.9.0 \
    pycco \
    websocket-client~=0.47.0 \
    planetmint-cryptoconditions>=0.9.4 \
    zenroom==2.0.0.dev1644927841 \
    blns

