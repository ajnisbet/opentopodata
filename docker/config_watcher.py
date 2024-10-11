import logging
import time
from pathlib import Path
import subprocess
import sys

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


# Paths.
CONFIG_DIR = Path("/app/")
CONFIG_PATH = Path("/app/config.yaml")
EXAMPLE_CONFIG_PATH = Path("/app/example-config.yaml")

# Debouncing: once the config has been reloaded, any queued unprocessed events should be discarded.
LAST_INVOCATION_TIME = time.time()


# Logger setup.
logger = logging.getLogger("configwatcher")
LOG_FORMAT = "%(asctime)s %(levelname)-8s %(message)s"
formatter = logging.Formatter(LOG_FORMAT)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
logger.addHandler(handler)


def run_cmd(cmd, shell=False):
    r = subprocess.run(cmd, shell=shell, capture_output=True)
    is_error = r.returncode != 0
    stdout = r.stdout.decode("utf-8")
    if is_error:
        logger.error(f"Error running command, returncode: {r.returncode}")
        logger.error("cmd:")
        logger.error(" ".join(cmd))
        if r.stdout:
            logger.error("stdout:")
            logger.error(stdout)
        if r.stderr:
            logger.error("stderr:")
            logger.error(r.stderr.decode("utf-8"))
        raise ValueError
    return stdout


def reload_config():
    global LAST_INVOCATION_TIME
    LAST_INVOCATION_TIME = time.time()
    logger.info("Restarting OTD due to config change.")
    run_cmd(["supervisorctl", "-c", "/app/docker/supervisord.conf", "stop", "uwsgi"])
    run_cmd(
        ["supervisorctl", "-c", "/app/docker/supervisord.conf", "restart", "memcached"]
    )
    run_cmd(["supervisorctl", "-c", "/app/docker/supervisord.conf", "start", "uwsgi"])
    run_cmd(
        ["supervisorctl", "-c", "/app/docker/supervisord.conf", "start", "warm_cache"]
    )
    LAST_INVOCATION_TIME = time.time()
    logger.info("Restarted OTD due to config change.")


class Handler(FileSystemEventHandler):

    def on_any_event(self, event):
        watch_paths_str = [
            EXAMPLE_CONFIG_PATH.as_posix(),
            CONFIG_PATH.as_posix(),
        ]

        # Filter unwanted events.
        if event.event_type not in {"modified", "created"}:
            logger.info(f"Dropping event with type {event.event_type=}")
            return
        if event.is_directory:
            logger.info(f"Dropping dir event")
            return
        if event.src_path not in watch_paths_str:
            logger.info(f"Dropping event with path {event.src_path=}")
            return
        if not Path(event.src_path).exists():
            logger.info(f"Dropping event for nonexistent path {event.src_path=}")
            return

        # Debouncing.
        mtime = Path(event.src_path).lstat().st_mtime
        if mtime < LAST_INVOCATION_TIME:
            msg = f"Dropping event for file that hasn't been modified since the last run. {event.src_path=}"
            logger.info(msg)
            return

        logger.info(f"Dispatching event on {event.src_path=}")
        reload_config()


if __name__ == "__main__":

    event_handler = Handler()
    observer = Observer()
    observer.schedule(event_handler, CONFIG_DIR, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()
