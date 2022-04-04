# Container for packages that need to be built from source but have massive dev dependencies.
FROM python:3.9.12-slim-bullseye as builder
RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        libmemcached-dev \
        patchelf \
        python3.9-dev

# pylibmc doesn't have wheels for >3.7
# (https://github.com/lericson/pylibmc/issues/269). Just building the wheel
# fails to pull in all the required libmemcached headers, this is fixed with
# auditwheel.
RUN pip config set global.disable-pip-version-check true && \
    pip wheel --wheel-dir=/root/wheels uwsgi==2.0.19.1 && \
    pip wheel --wheel-dir=/root/wheels regex==2021.11.10 && \
    pip wheel --wheel-dir=/tmp/wheels pylibmc==1.6.1 && \
    pip install --no-cache-dir auditwheel && \
    auditwheel repair /tmp/wheels/pylibmc-*.whl -w /root/wheels --plat manylinux_2_27_x86_64

# The actual container.
FROM python:3.9.12-slim-bullseye
RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        nginx \
        memcached \
        supervisor && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/wheels /root/wheels
COPY requirements.txt /app/requirements.txt
RUN pip install \
        --no-index \
        --no-cache-dir \
        --disable-pip-version-check \
        --find-links=/root/wheels \
        uwsgi regex pylibmc && \
    pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt && \
        rm -rf /root/.cache/pip/* && \
        rm root/wheels/* && \
        rm /app/requirements.txt

WORKDIR /app
COPY . /app/

RUN echo > /etc/nginx/sites-available/default && \
    cp /app/docker/nginx.conf /etc/nginx/conf.d/nginx.conf && \
    cp /app/docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

CMD ["sh", "/app/docker/run.sh"]
EXPOSE 5000

ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV GDAL_DISABLE_READDIR_ON_OPEN=TRUE
ENV GDAL_NUM_THREADS=ALL_CPUS
ENV GDAL_CACHEMAX=512
