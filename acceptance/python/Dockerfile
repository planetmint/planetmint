FROM python:3.9

RUN apt-get update \
    && pip install -U pip \
    && apt-get autoremove \
    && apt-get clean
RUN apt-get install -y vim zsh build-essential cmake

RUN mkdir -p /src
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install --upgrade meson ninja
RUN pip install zenroom==2.0.0.dev1644927841
RUN pip install --upgrade \
	pycco \
	websocket-client~=0.47.0 \
	pytest~=3.0 \
	# planetmint-cryptoconditions>=0.9.4\
	# planetmint-driver>=0.9.0 \
	git+https://github.com/planetmint/cryptoconditions.git@asset-migration  \
	git+https://github.com/planetmint/planetmint-driver-python.git@asset-migration \
	blns
