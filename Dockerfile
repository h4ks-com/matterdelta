FROM python:3.11-alpine

RUN apk add --no-cache libgcc libstdc++

RUN pip install --no-cache-dir matterdelta

VOLUME /data
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
