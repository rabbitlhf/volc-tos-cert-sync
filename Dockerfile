FROM python:3.13-alpine AS builder

LABEL maintainer="Fundy <rabbitlhf@gmail.com>"
LABEL description="火山引擎TOS证书同步工具 - Apache-2.0 许可证"

ENV TIMEZONE="Asia/Shanghai" \
    VOLC_REGION="cn-guangzhou" \
    VOLC_PROJECT="Production" \
    CERT_CRT_PATH="/etc/cert/tls.crt" \
    CERT_KEY_PATH="/etc/cert/tls.key" \
    CONFIG_PATH="/etc/volc_tos_sync/config.env" \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .

RUN set -ex && \
    apk add --no-cache gcc musl-dev libffi-dev openssl-dev ca-certificates && \
    mkdir -p /app /etc/cert /etc/volc_tos_sync && \
    chmod 700 /etc/cert /etc/volc_tos_sync && \
    cd /app && \
    pip install -r requirements.txt && \
    rm -rf /var/cache/apk/* /root/.cache/pip && \
    apk del gcc musl-dev libffi-dev openssl-dev


COPY volc_tos_cert_sync/ /app/volc_tos_cert_sync/

ENTRYPOINT ["/bin/sh", "-c", "if [ -f $CONFIG_PATH ]; then source $CONFIG_PATH; fi && python -m volc_tos_cert_sync"]
