# Running Open Topo Data on Windows

A few users have mentioned that the [getting started](/server/) instructions don't work on Windows. This is difficult for me to debug without access Windows machine, but I believe the instructions below will work.

## Getting started on Windows

Install [docker](https://hub.docker.com/editions/community/docker-ce-desktop-windows) and [git](https://git-scm.com/download/win).

Make sure docker is running. The command `docker ps` should print a (possibly empty) table of containers, rather than an error message.

Clone the repository with

```bash
git clone https://github.com/ajnisbet/opentopodata.git
```


and change into the repo folder

```
cd opentopodata
```

To build the docker image, instead of using of `make build`, build with 

```bash
docker build --tag opentopodata --file docker/Dockerfile .
```


To run the server, instead of using `make run`, run with

```
docker run --rm -it --volume "C:/path/to/opentopodata/data:/app/data:ro" -p 5000:5000 -e N_UWSGI_THREADS=8 opentopodata sh -c "/usr/bin/supervisord -c /app/docker/supervisord.conf"
```

Modify `-e N_UWSGI_THREADS=8` in the `docker run` command above with the number of logical CPU cores on your system. Open Topo Data is [CPU bound](/notes/performance-optimisation/) for most compressed datasets.

Also modify `C:/path/to/opentopodata/data` in that command with the path to the folder containing your datasets.



## Troubleshooting

### Error during connect

An error like 

<pre style="white-space : pre-wrap; padding: .525rem .6rem;">
error during connect: Get http://%2F%2F.%2Fpipe%2Fdocker_engine/v1.40/containers/json: open //./pipe/docker_engine: The system cannot find the file specified. In the default daemon configuration on Windows, the docker client must be run elevated to connect. This error may also indicate that the docker daemon is not running.
</pre>
means docker isn't running.



### The input device is not a TTY

Trying to run the `docker run` command in Git CMD gives me this error:

<pre style="white-space : pre-wrap; padding: .525rem .6rem;">
the input device is not a TTY.  If you are using mintty, try prefixing the command with 'winpty'
</pre>

Run the `docker run` command in Command Prompt instead.


### Could not find config file

Errors complaining about not finding `/app/docker/supervisord.conf` like

<pre style="white-space : pre-wrap; padding: .525rem .6rem;">
process_begin: CreateProcess(NULL, pwd, ...) failed.
Makefile:8: pipe: No such file or directory
Error: could not find config file /app/docker/supervisord.conf
For help, use /usr/bin/supervisord -h
make: *** [Makefile:8: run] Error 2
</pre>

or 

<pre style="white-space : pre-wrap; padding: .525rem .6rem;">
docker: Error response from daemon: OCI runtime create failed: container_linux.go:349: starting container process caused "exec: \"exec /usr/bin/supervisord -c /app/docker/supervisord.conf\": stat exec /usr/bin/supervisord -c /app/docker/supervisord.conf: no such file or directory": unknown.
</pre>

should be fixed in v1.3.1 and greater, or might mean you're using `make` instead of the commands above.