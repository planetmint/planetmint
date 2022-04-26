FROM python:3.9

RUN apt-get update \
    && pip install -U pip \
    && apt-get autoremove \
    && apt-get clean
RUN apt-get install -y vim zsh build-essential cmake

RUN mkdir -p /src
RUN pip install --upgrade meson ninja
RUN pip install --upgrade \
	pycco \
	websocket-client~=0.47.0 \
	pytest~=3.0 \
	git+https://github.com/planetmint/cryptoconditions.git@gitzenroom  \
	git+https://github.com/planetmint/planetmint-driver.git@gitzenroom \
	#planetmint-cryptoconditions>=0.9.0\
	#planetmint-driver>=0.9.0 \
	blns
	
	


#FROM python:3.9
#
#RUN apt-get update && apt-get install -y vim zsh
#RUN apt-get update \
#    && apt-get install -y git zsh\
#    && pip install -U pip \
#    && apt-get autoremove \
#    && apt-get clean	
#RUN apt install sudo
#RUN apt-get install -y python3 openssl ca-certificates git python3-dev
#RUN apt-get install zsh gcc
#RUN apt-get install libffi-dev  
#RUN apt-get install build-essential cmake -y
#
#
#RUN mkdir -p /src
#RUN pip install --upgrade \
#	pycco \
#	websocket-client~=0.47.0 \
#	pytest~=3.0 \
#	planetmint-driver>=0.9.0 \
#	blns \
#	git+https://github.com/planetmint/cryptoconditions.git@gitzenroom >=0.9.0 \
#	chardet==3.0.4 \
#    aiohttp==3.7.4 \
#    abci==0.8.3 \
#    #planetmint-cryptoconditions>=0.9.0\
#    flask-cors==3.0.10 \
#    flask-restful==0.3.9 \
#    flask==2.0.1 \
#    gunicorn==20.1.0 \
#    jsonschema==3.2.0 \
#    logstats==0.3.0 \
#    packaging>=20.9 \
#    pymongo==3.11.4 \
#    pyyaml==5.4.1 \
#    requests==2.25.1 \
#    setproctitle==1.2.2
#
