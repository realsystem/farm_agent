FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache python3 py3-pip

RUN python3 -m pip install --no-cache-dir --break-system-packages openai-agents

COPY agent.py /
COPY run.sh /

RUN chmod a+x /run.sh

LABEL \
    io.hass.version="0.4.0" \
    io.hass.type="app" \
    io.hass.arch="aarch64|amd64"

CMD ["/run.sh"]