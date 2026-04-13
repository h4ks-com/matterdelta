FROM python:3.11-alpine

RUN apk add --no-cache libgcc libstdc++

RUN pip install --no-cache-dir matterdelta

VOLUME /data
COPY entrypoint.sh /entrypoint.sh
COPY setup_groups.py /setup_groups.py
COPY init_account.py /init_account.py
COPY apply_config.py /apply_config.py
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
