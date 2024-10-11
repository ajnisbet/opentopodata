import logging
import time
import warm_cache

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from pymemcache.client.base import Client


#Connect to memcached socket. Since this is hardcoded in the supervisored.conf it shouldn't change that much
memcacheClient = Client("/tmp/memcached.sock")


def reload_config():
    logging.error("config.yaml changes. Restarting uswgi and memcached to make the changes")
    #Restart uwsgi
    #TODO
    #Flush memcache using pymemcached
    memcacheClient.flush_all()
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
