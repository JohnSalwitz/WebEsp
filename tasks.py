import threading
import time
import requests

#
# Low tech way to run a background task after the server starts up.
#
class Backgrounder:

    def __init__(self):
        self.worker = None
        self.delay = None
        self.started = False

    def start_worker(self, worker, delay):
        self.worker = worker
        self.delay = delay
        thread = threading.Thread(target=self._worker)
        thread.start()

    # waits for server to startup then starts task.
    def _worker(self):
        while True:
            time.sleep(0.5)
            try:
                r = requests.get('http://127.0.0.1:5000/')
                if r.status_code == 200:
                    break
            except:
                pass

        if not self.started:
            self.started = True
            while True:
                self.worker()
                time.sleep(self.delay)
