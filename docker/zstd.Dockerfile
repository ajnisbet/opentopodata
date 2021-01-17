# Container for packages that need to be built from source but have massive dev dependencies.
FROM python:3.7.7-slim-buster as builder
RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        python3.7-dev
RUN pip wheel --wheel-dir=/root/wheels uwsgi==2.0.18 && \
    pip wheel --wheel-dir=/root/wheels regex==2020.10.23

# The actual container.
FROM python:3.7.7-slim-buster
RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        g++ \
        gcc \
        libsqlite3-dev \
        libtiff5-dev \
        memcached \
        nginx \
        pkg-config \
        sqlite3 \
        wget \
        zstd \
        supervisor && \
    rm -rf /var/lib/apt/lists/*

## Install proj.
RUN wget https://download.osgeo.org/proj/proj-7.2.0.tar.gz  &&\
    tar xvzf proj-7.2.0.tar.gz  &&\
    cd proj-7.2.0  &&\
    ./configure \
        --without-curl  &&\
    make && make install



RUN set -e && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        libgeos-dev \
        liblzma-dev \
        libpng-dev  \
        libzstd-dev  \
        unzip && \
    rm -rf /var/lib/apt/lists/*

## Install gdal.
RUN wget download.osgeo.org/gdal/3.0.4/gdal304.zip
RUN unzip gdal304.zip  &&\
    cd gdal-3.0.4  &&\
    ./configure  \
    --with-proj \
    --with-zstd \
    --with-geotiff=internal \
    --with-libtiff=internal \
    --with-libz=internal \
    --without-cfitsio \
    --without-cryptopp \
    --without-curl \
    --without-ecw \
    --without-expat \
    --without-fme \
    --without-freexl \
    --without-geos \
    --without-gif \
    --without-gif \
    --without-gnm \
    --without-grass \
    --without-hdf4 \
    --without-hdf5 \
    --without-idb \
    --without-ingres \
    --without-jasper \
    --without-jp2mrsid \
    --without-kakadu \
    --without-libgrass \
    --without-libkml \
    --without-mrsid \
    --without-mysql \
    --without-netcdf \
    --without-odbc \
    --without-ogdi \
    --without-openjpeg \
    --without-pcidsk \
    --without-pcraster \
    --without-pcre \
    --without-perl \
    --without-pg \
    --without-pg \
    --without-qhull \
    --without-sde \
    --without-spatialite \
    --without-xerces \
    --without-xml2 &&\
    make clean && make -j8 && make install

# Set LD_LIBRARY_PATH so that recompiled GDAL is used
ENV LD_LIBRARY_PATH="/usr/local/lib"



COPY --from=builder /root/wheels /root/wheels
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip &&\
    pip install \
        --no-index \
        --no-cache-dir \
        --find-links=/root/wheels \
        uwsgi regex && \
    pip install --no-cache-dir --no-binary rasterio numpy rasterio==1.1.8  &&\
    pip install --no-cache-dir -r /app/requirements.txt && \
        rm -rf /root/.cache/pip/* && \
        rm root/wheels/* && \
        rm /app/requirements.txt

WORKDIR /app
COPY . /app/

RUN echo > /etc/nginx/sites-available/default && \
    cp /app/docker/nginx.conf /etc/nginx/conf.d/nginx.conf && \
    cp /app/docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

RUN mkdir -p /usr/local/nginx/html/ && cp /app/deploy/rate_limit_exceeded.json /usr/local/nginx/html/
ENV GDAL_DISABLE_READDIR_ON_OPEN=TRUE

CMD ["sh", "/app/docker/run.sh"]
EXPOSE 5000
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
