# Container for packages that need to be built from source but have massive dev dependencies.
FROM python:3.11.10-slim-bookworm as builder
RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        python3.11-dev \
        gdal-bin \
        libgdal-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt

RUN pip config set global.disable-pip-version-check true && \
    pip install --upgrade pip wheel && \
    pip install 'setuptools<67' && \
    pip install numpy==1.26.4 Cython && \
    pip wheel --wheel-dir=/root/wheels uwsgi==2.0.28 && \
    pip wheel --wheel-dir=/root/wheels regex==2024.11.6 && \
    pip wheel --wheel-dir=/root/wheels --no-build-isolation --no-deps rasterio==1.3.11 && \
    pip wheel --wheel-dir=/root/wheels --no-build-isolation --no-deps pyproj==3.7.1 && \
    pip wheel --wheel-dir=/root/wheels --no-build-isolation --no-deps pylibmc==1.6.3 

# The actual container.
FROM python:3.11.10-slim-bookworm
RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        inotify-tools \
        nano \
        nginx \
        memcached \
        supervisor \
        gdal-bin \
        libgdal-dev \
        gcc \
        g++ && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/wheels /root/wheels
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --disable-pip-version-check --upgrade pip setuptools wheel && \
    pip install \
        --no-cache-dir \
        --disable-pip-version-check \
        --find-links=/root/wheels \
        --prefer-binary \
        -r /app/requirements.txt && \
        rm -rf /root/.cache/pip/* && \
        rm -rf /root/wheels/* && \
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
