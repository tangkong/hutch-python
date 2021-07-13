import dataclasses
import logging
import sys
from contextlib import contextmanager
from queue import Queue
from typing import Any

import pytest

from hutch_python.ipython_log import INPUT_LEVEL, IPythonLogger
from hutch_python.ipython_log import logger as ipython_logger

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def fake_ipython():
    # Clear the sys errors, potentially from previous tests
    try:
        del sys.last_type
        del sys.last_value
        del sys.last_traceback
    except AttributeError:
        pass
    return FakeIPython()


class FakeIPythonEvents:
    def __init__(self):
        self.callbacks = {}

    def register(self, name, callback):
        self.callbacks.setdefault(name, []).append(callback)
        logger.info("Registered callback %s %s", name, callback)


@dataclasses.dataclass
class FakeIPythonInfo:
    raw_cell: str


@dataclasses.dataclass
class FakeIPythonResult:
    info: FakeIPythonInfo
    result: Any
    error_in_exec: bool


class FakeIPython:
    def __init__(self):
        self.user_ns = dict(In=[""])
        self.events = FakeIPythonEvents()

    def add_line(self, in_line, out_line=None, is_error=False):
        line_number = len(self.user_ns["In"])
        info = FakeIPythonInfo(raw_cell=in_line)
        result = FakeIPythonResult(
            info=info, result=out_line, error_in_exec=is_error
        )
        logger.info(f"Adding line: {line_number} {in_line} -> {out_line}")
        for cb in self.events.callbacks.get("pre_run_cell", []):
            logger.info(f"Calling {cb.__name__} with args {info}")
            cb(info)
        self.user_ns["In"].append(in_line)
        for cb in self.events.callbacks.get("post_run_cell", []):
            logger.info(f"Calling {cb.__name__} with args {result}")
            cb(result)


@contextmanager
def restore_logging():
    prev_handlers = list(ipython_logger.handlers)
    yield
    ipython_logger.handlers = prev_handlers


@pytest.fixture(scope='function')
def log_queue():
    with restore_logging():
        my_queue = Queue()
        debug_handler = logging.StreamHandler(sys.stdout)
        debug_handler.setLevel(INPUT_LEVEL)
        ipython_logger.addHandler(debug_handler)

        handler = logging.handlers.QueueHandler(my_queue)
        handler.setLevel(INPUT_LEVEL)
        ipython_logger.addHandler(handler)
        yield my_queue


@pytest.mark.timeout(5)
def test_ipython_logger(log_queue, fake_ipython):
    ipython_logger.debug('test_ipython_logger')
    ipylog = IPythonLogger(fake_ipython)
    while not log_queue.empty():
        log_queue.get(block=False)

    logger.info("Sanity check: ensuring the queue handler works")
    ipython_logger.debug('hello')
    assert 'hello' in log_queue.get().getMessage()
    # We should do nothing if log gets called too early
    assert log_queue.empty()

    logger.info("One logged In, no output")
    fake_ipython.add_line('print(5)')
    assert 'In  [1]: print(5)' in log_queue.get(block=False).getMessage()
    assert log_queue.empty()

    logger.info("One logged In, one Out")
    fake_ipython.add_line('1 + 1', 2)
    assert 'In  [2]: 1 + 1' in log_queue.get(block=False).getMessage()
    assert 'Out [2]: 2' in log_queue.get(block=False).getMessage()
    assert log_queue.empty()

    logger.info("Set up a ZeroDivisionError for logging")
    try:
        1/0
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()

    # Force in our exception information, despite the fact that we just handled
    # it above
    sys.last_type = exc_type
    sys.last_value = exc_value
    sys.last_traceback = exc_traceback

    fake_ipython.add_line('1/0', is_error=True)

    assert 'In  [3]: 1/0' in log_queue.get(block=False).getMessage()
    assert "Exception details" in log_queue.get(block=False).getMessage()

    logger.info("OK, now forcing a failure by tweaking internals")
    ipylog.ipython_in = None
    fake_ipython.add_line('something')
    assert 'Logging error' in log_queue.get(block=False).getMessage()
