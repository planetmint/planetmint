FROM python:3.9

RUN apt-get update \
    && pip install -U pip \
    && apt-get autoremove \
    && apt-get clean
RUN apt-get install -y vim 
RUN apt-get update
RUN apt-get install -y build-essential cmake openssh-client openssh-server git
RUN apt-get install -y zsh

RUN mkdir -p /src
RUN pip install --upgrade meson ninja
RUN pip install --upgrade \
    pytest~=6.2.5 \
    pycco \
    websocket-client~=0.47.0 \
    planetmint-cryptoconditions>=0.10.0 \
    planetmint-driver>=9.2.0 \
    blns
RUN pip install base58 pynacl==1.4.0 zenroom==2.1.0.dev1655293214 pyasn1==0.4.8 cryptography==3.4.7
