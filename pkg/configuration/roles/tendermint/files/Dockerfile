ARG tm_version=v0.34.24
FROM tendermint/tendermint:${tm_version}
LABEL maintainer "contact@ipdb.global"
WORKDIR /
USER root
RUN apk --update add bash
ENTRYPOINT ["/usr/bin/tendermint"]
