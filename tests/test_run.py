import json
import os
import subprocess
import time

import pylibmc
import requests

MEMCACHED_SOCKET = "/tmp/memcached.sock"
UWSGI_SOCKET = "/tmp/uwsgi.sock"


class TestRun:
    def setup_class(self):
        subprocess.run("env -u DISABLE_MEMCACHE sh /app/docker/run.sh &", shell=True)
        for i in range(60):
            time.sleep(1)
            if os.path.exists(MEMCACHED_SOCKET) and os.path.exists(UWSGI_SOCKET):
                break
        else:
            raise RuntimeError("Memcached and uwsgi not started within 60s.")

    def test_200(self):
        url = "http://localhost:5000/v1/test-dataset?locations=1,1"
        response = requests.get(url)
        rjson = response.json()
        assert response.status_code == 200
        assert rjson["status"] == "OK"
        assert len(rjson["results"]) == 1
        assert response.headers["x-opentopodata-version"]

    def test_memcache(self):
        url = "http://localhost:5000/v1/test-dataset?locations=1,1"
        response = requests.get(url)
        client = pylibmc.Client([MEMCACHED_SOCKET])
        stats = client.get_stats()[0][1]
        assert int(stats["curr_items"]) > 0

    def test_gzip(self):
        locations = "|".join(
            ["13.345,32.345"] * 50
        )  # Lots of locations to make response longer than min gzip size.
        url = "http://localhost:5000/v1/test-dataset?locations=" + locations
        response = requests.get(url)
        assert response.headers.get("content-encoding") == "gzip"
