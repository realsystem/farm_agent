FROM ghcr.io/home-assistant/base:latest

RUN apk add --no-cache python3

COPY agent.py /
COPY run.sh /

RUN chmod a+x /run.sh

CMD ["/run.sh"]
