exec env N_UWSGI_THREADS=$(nproc --all) /usr/bin/supervisord -c /app/docker/supervisord.conf
