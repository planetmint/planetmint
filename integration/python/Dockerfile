FROM python:3.9

RUN mkdir -p /src
RUN pip install --upgrade \
    pytest~=6.2.5 \
    planetmint-driver~=0.9.0
RUN apt-get update && apt-get install -y openssh-client openssh-server