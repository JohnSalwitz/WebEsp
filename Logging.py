import logging
import queue
import socket
from unittest import TestCase


#
# Custom logger --
# Q's log messages (print optional) for retreval by remote client
# Stores log messages as json
# Adds custom field(s) -- including url of logger
#
class JSONLogger:
    _log_keys = ["asctime", "levelname", "message", "url"]
    _max_queue_size = 256
    _max_response_msg = 120

    def __init__(self):

        # create logger with 'spam_application'
        self._logger = logging.getLogger('spam_application')
        self._logger.setLevel(logging.INFO)

        # create console handler with a higher log level
        self._stream_handler = logging.StreamHandler(self)
        self._stream_handler.setFormatter(self.formatter())
        self._logger.addHandler(self._stream_handler)

        self._url = socket.gethostbyname(socket.gethostname())
        self._log_queue = queue.Queue()
        self._log_queue_length = 0
        self._verbose = False

    def formatter(self):
        # creates formatter so logger outputs a json blob...
        jform = "|".join(["{}:%({})s".format(f, f) for f in self._log_keys])
        return logging.Formatter(jform)

    # stores in json.  This is not pretty.
    def write(self, msg):
        if msg != '\n':
            parts = msg.split("|")
            d = {}
            for part in parts:
                s = part.split(":", 1)
                d[s[0]] = s[1]
            if self._verbose:
                print(d)
            if self._log_queue.qsize() == self._max_queue_size:
                self._log_queue.get()
            self._log_queue.put(d)
            self._log_queue_length += 1

    def flush(self):
        pass

    def setLevel(self, level):
        self._logger.setLevel(level)

    def verbose(self, enable = True):
        self._verbose = enable

    def error(self, msg, url=None):
        url = url or self._url
        self._logger.error(msg, extra={"url": url})

    def warning(self, msg, url=None):
        url = url or self._url
        self._logger.warning(msg, extra={"url": url})

    def debug(self, msg, url=None):
        url = url or self._url
        self._logger.debug(msg, extra={"url": url})

    def info(self, msg, url=None):
        url = url or self._url
        self._logger.info(msg, extra={"url": url})

    # logs a flask request...
    def flask_request(self, request, argument, response):
        if len(response) > self._max_response_msg:
            response = response[:self._max_response_msg] + "..."
        self.debug("{} \"{}\" ---> {}".format(request.path, argument, response), url=request.remote_addr)

    # call error message directly
    def event(self, level, msg, url=None):
        m = getattr(self, level)
        m(msg, url)

    def set_max_q_size(self, size):
        self._max_queue_size = size

    def rows(self, offset=0):
        base = self._log_queue_length - self._log_queue.qsize()
        lst = list(self._log_queue.queue)
        offset = max(offset - base, 0)
        return lst[offset:]


# Instantiate logger...
# to do: unify FLASK logger with JSONLogger
jlog = JSONLogger()
jlog.setLevel(logging.DEBUG)
jlog.verbose(True)
jlog.debug("Start Of Logging")


class TestJSONLogger(TestCase):

    def setUp(self):
        self.jlog = JSONLogger()
        self.jlog.setLevel(logging.DEBUG)
        self.jlog.verbose(True)

    def test_error(self):
        self.jlog.verbose(False)
        self.jlog.error("this is error")
        print("-----")

    def test_warning(self):
        self.jlog.warning("this is warning")

    def test_debug(self):
        self.jlog.debug("this is debug")

    def test_info(self):
        self.jlog.info("this is info")

    def test_rows(self):
        self.jlog.setLevel(logging.DEBUG)

        self.jlog.event("info", "Row 1")
        self.jlog.event("info", "Row 2")
        self.jlog.event("info", "Row 3")
        self.jlog.event("info", "Row 4")
        self.jlog.event("info", "Row 5")
        self.jlog.event("info", "Row 6")
        rows = self.jlog.rows(4)
        for row in rows:
            print(row)
        self.assertEqual(len(rows), 2)
