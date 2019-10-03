FROM python:3.7.4-slim-buster as builder

RUN set -e && \
    apt-get update && \
    apt-get full-upgrade -y && \
    apt-get install -y \
        gcc
RUN pip wheel --wheel-dir=/root/wheels uwsgi

FROM python:3.7.4-slim-buster

RUN set -e && \
    apt-get update && \
    apt-get full-upgrade -y && \
    apt-get install -y \
        nginx \
        memcached \
        supervisor && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/wheels /root/wheels
COPY requirements.txt /app/requirements.txt
RUN pip install \
    --no-index \
    --no-cache-dir \
    --find-links=/root/wheels \
    uwsgi && \
pip install pylibmc --no-cache-dir && \
pip install --no-cache-dir -r /app/requirements.txt && \
    rm -rf /root/.cache/pip/* && \
    rm root/wheels/* && \
    rm /app/requirements.txt

WORKDIR /app
COPY . /app/

RUN echo > /etc/nginx/sites-available/default && \
    cp /app/docker/nginx.conf /etc/nginx/conf.d/nginx.conf && \
    cp /app/docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD sh /app/docker/run.sh
EXPOSE 5000
