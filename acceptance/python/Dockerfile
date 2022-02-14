FROM python:3.9

RUN apt-get update && apt-get install -y vim zsh
RUN mkdir -p /src
RUN pip install --upgrade \
	pycco \
	websocket-client~=0.47.0 \
	pytest~=3.0 \
	planetmint-driver>=0.9.0 \
	blns \
	planetmint-cryptoconditions>=0.9.0
