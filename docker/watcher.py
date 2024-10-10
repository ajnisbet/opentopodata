import logging
import time
import os
import warm_cache

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def reload_config():
    logging.info("config.yaml changes. Restarting uswgi and memcached to make the changes")
    # Kill all uwsgi instances with SIGTERM
    os.system("kill -15 `pidof uwsgi`")
    # Flush memcache with restarting it. Without nc/telnet thats the best solution
    os.system("service memcached restart")
    # Restart uwsgi. Amount of processes stolen from run.sh
    os.system("/usr/local/bin/uwsgi --ini /app/docker/uwsgi.ini --processes $(nproc --all)")
    warm_cache

class Handler(FileSystemEventHandler):

    def on_created(self, event):
       reload_config()
    def on_modified(self, event):
        reload_config()





CONFIG_PATH = "/app/config.yaml"
EXAMPLE_CONFIG_PATH = "/app/example-config.yaml"

if __name__ == "__main__":
    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, CONFIG_PATH)
    observer.schedule(event_handler, EXAMPLE_CONFIG_PATH)
    observer.start()
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
