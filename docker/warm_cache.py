import logging
import os
import sys
import time


MAX_WAIT_S = 60
MEMCACHED_SOCKET = '/tmp/memcached.sock'

# Wait til memcache has started by checking the socket exists. Then run all
# the cached function calls.
if __name__ == '__main__':

    for i in range(MAX_WAIT_S):
        time.sleep(1)
        if not os.path.exists(MEMCACHED_SOCKET):
            continue

        sys.path.append('/app/')
        from opentopodata import api
        
        api._load_config()
        api._load_datasets()
        logging.info('Warmed cache')
        break

    else:
        logging.warning('Unable to warm cache')

