FROM python:3.9
LABEL maintainer "contact@ipdb.global"
RUN mkdir -p /usr/src/app
COPY . /usr/src/app/
WORKDIR /usr/src/app
RUN apt-get -qq update \
    && apt-get -y upgrade \
    && apt-get install -y jq vim zsh build-essential cmake\
    && pip install . \
    && pip install pynacl==1.4.0 base58==2.1.1 pyasn1==0.4.8 zenroom==2.1.0.dev1655293214 cryptography==3.4.7\
    && apt-get autoremove \
    && apt-get clean

VOLUME ["/data", "/certs"]

ENV PYTHONUNBUFFERED 0
ENV PLANETMINT_CONFIG_PATH /data/.planetmint
ENV PLANETMINT_SERVER_BIND 0.0.0.0:9984
ENV PLANETMINT_WSSERVER_HOST 0.0.0.0
ENV PLANETMINT_WSSERVER_SCHEME ws
ENV PLANETMINT_WSSERVER_ADVERTISED_HOST 0.0.0.0
ENV PLANETMINT_WSSERVER_ADVERTISED_SCHEME ws
ENV PLANETMINT_WSSERVER_ADVERTISED_PORT 9985
ENTRYPOINT ["planetmint"]
CMD ["start"]
