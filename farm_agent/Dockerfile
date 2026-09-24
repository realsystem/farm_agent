FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache python3 py3-pip

RUN pip3 install --no-cache-dir openai-agents

COPY agent.py /
COPY run.sh /

RUN chmod a+x /run.sh

LABEL \
    io.hass.version="0.2.0" \
    io.hass.type="app" \
    io.hass.arch="aarch64|amd64"

CMD ["/run.sh"]