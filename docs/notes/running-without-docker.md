# Running without Docker

Open Topo Data uses docker to manage dependencies, builds, and processes. Containerisation is especially helpful in the geospatial domain, where compatibility between system libraries, compiled packages, and python scripts is flakey. 

So I highly recommend running Open Topo Data with docker, it saves me a bunch of headaches. But if you've read this far you already know that 🐉.

## Running Open Topo Data 1.5.0 on Debian 10

A user (thanks [Luca](https://www.lucabert.de/)!) was able to get Open Topo Data running on Debian 10 without docker and was kind enough to share their instructions.

### Minimal install

Download Open Topo Data.

```bash
git clone https://github.com/ajnisbet/opentopodata.git
cd opentopodata
```

Install system dependencies

```bash
apt install gcc python3.7-dev python3-pip
```

Debian 10 comes with an old version of pip, it needs to be updated:

```bash
pip3 install --upgrade pip
```

For some reason `pyproj` needs to be installed on its own, otherwise it will use the outdated system PROJ library instead of the packaged wheel version. Find the version of `pyproj` required

```bash
cat requirements.txt | grep pyproj
```

and install that pinned version

```bash
pip3 install pyproj==3.0.0.post1
```

then the remaining python packages can be installed:

```bash
pip3 install -r requirements.txt
```

This should give a minimal install of Open Topo Data that can be started with 

```bash
FLASK_APP=opentopodata/api.py DISABLE_MEMCACHE=1 flask run --port 5000
```

### Full install

The minimal instructions above install Open Topo Data without memcache or a web server. This is fine if you have a small dataset, few requests per second, and don't expose the insecure flask server to the internet. 

For a faster and more secure server, you can install memcache and uwsgi, and run the service with systemd.

Install some more dependencies:

```bash
apt install memcached
pip3 install regex uwsgi
```

Set up memcached. On Debian 10, memcached comes with "PrivateTemp" enabled, which prevents saving the socket where Open Topo Data expects it:


```bash
usermod -g www-data memcache
mkdir -p /etc/systemd/system/memcached.service.d/
echo -e "[Service]\n\nPrivateTmp=false" > /etc/systemd/system/memcached.service.d/override.conf
systemctl daemon-reload
echo -e "-s /tmp/memcached.sock\n-a 0775\n-c 1024\n-I 8m" >> /etc/memcached.conf
service memcached restart
```


Create a file `uwsgi.ini` somewhere, say `/home/opentopodata/uwsgi.ini`, that points to the repo you downloaded:

```ini
[uwsgi]
strict = true
need-app = true

http-socket = :9090
vacuum = true
uid = www-data
gid = www-data

master = true

chdir = /home/opentopodata
pythonpath = /home/opentopodata
wsgi-file = /home/opentopodata/opentopodata/api.py
callable = app
manage-script-name = true

die-on-term = true

buffer-size = 65535
```

If uwsgi works with 
```bash
/usr/local/bin/uwsgi --ini /home/opentopodata/uwsgi.ini --processes 10s
```

Then you can create a systemd script in `/etc/systemd/system/opentopodata.service`:


```ini
[Unit]
Description=OpenTopoData web application
After=network.target

[Service]
User=www-data
WorkingDirectory=/home/opentopodata
ExecStart=/usr/local/bin/uwsgi /home/opentopodata/uwsgi.ini --processes 10s
Restart=always

[Install]
WantedBy=multi-user.target
```

Then manage Open Topo Data with

```txt
systemctl daemon-reload 
systemctl enable opentopodata.service 
systemctl start opentopodata.service 
```