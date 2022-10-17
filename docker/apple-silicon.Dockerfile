# Some geo dependencies (like rasterio) don't have wheels that work for M1
# macs. So this image includes gdal, as well as other dependicies needed to
# build those libraries from scratch.
#
# It works just the same as the main image, but is much larger and slower to
# build.

FROM osgeo/gdal:ubuntu-full-3.5.2
RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        nginx \
        memcached \
        python3-pip \
        gcc \
        g++ \
        supervisor \
        libmemcached-dev \
        python3.8-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install \
        --no-cache-dir \
        --disable-pip-version-check \
        uwsgi regex pylibmc && \
    pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt && \
        rm -rf /root/.cache/pip/* && \
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