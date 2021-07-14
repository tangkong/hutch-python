import dataclasses
import logging
import sys
from queue import Empty, Queue
from typing import Any, Dict, List, Optional

import pytest

from hutch_python.ipython_log import IPythonLogger
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
class FakeExecutionInfo:
    """A set of information which comes out of pre_run_cell."""
    # raw_cell is the user-executed code, and all we really care about
    raw_cell: str
    store_history: bool = False
    silent: bool = False
    shell_futures: bool = True


@dataclasses.dataclass
class FakeExecutionResult:
    """A result which comes out of post_run_cell."""
    info: FakeExecutionInfo
    result: Any
    error_in_exec: bool
    execution_count: int = 0
    error_before_exec: bool = False


class FakeIPython:
    """A fake replacement of IPython's ``TerminalInteractiveShell``."""
    user_ns: Dict[str, Any]
    events: FakeIPythonEvents

    def __init__(self):
        self.user_ns = dict(In=[""])
        self.events = FakeIPythonEvents()

    def add_line(self, in_line, out_line=None, is_error=False):
        line_number = len(self.user_ns["In"])
        info = FakeExecutionInfo(raw_cell=in_line)
        result = FakeExecutionResult(
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


@pytest.fixture(scope='function')
def ipylog(log_queue, fake_ipython) -> IPythonLogger:
    """IPythonLogger instance, with a promise of an empty initial queue."""
    ipylog = IPythonLogger(fake_ipython)
    while not log_queue.empty():
        log_queue.get(block=False)
    yield ipylog


def next_pertinent_log_record(
    queue: Queue,
    pertinent_loggers: Optional[List[str]] = None
) -> logging.LogRecord:
    """
    Get the next relevant log record from the queue.

    Parameters
    ----------
    queue : queue.Queue
        The queue to search.

    pertinent_loggers : list of str, optional
        List of logger names that are relevant.
        Defaults to what is being tested in this module - the IPythonLogger
        logger instance.

    Returns
    -------
    record : logging.LogRecord
        The matching record.

    Raises
    ------
    Empty
        If the queue is empty and no relevant messages are available.
    """
    pertinent_loggers = pertinent_loggers or {
        "hutch_python.ipython_log",
    }
    while not queue.empty():
        item = queue.get(block=False)
        if item.name in pertinent_loggers:
            return item

    raise Empty(f"No relevant messages available for {pertinent_loggers}")


def next_pertinent_log_message(
    queue: Queue,
    pertinent_loggers: Optional[List[str]] = None
) -> str:
    """
    Get the next relevant log message from the queue.

    Convenience wrapper around :func:`next_pertinent_log_record`.

    Parameters
    ----------
    queue : queue.Queue
        The queue to search.

    pertinent_loggers : list of str, optional
        List of logger names that are relevant.
        Defaults to what is being tested in this module - the IPythonLogger
        logger instance.

    Returns
    -------
    message : str
        The matching record's message.

    Raises
    ------
    Empty
        If the queue is empty and no relevant messages are available.
    """
    record = next_pertinent_log_record(
        queue, pertinent_loggers=pertinent_loggers
    )
    return record.getMessage()


def assert_no_more_messages(
    queue: Queue,
    pertinent_loggers: Optional[List[str]] = None
) -> None:
    """
    Assert that no more relevant messages are available from a queue.

    Convenience wrapper around :func:`next_pertinent_log_record`.

    Parameters
    ----------
    queue : queue.Queue
        The queue to search.

    pertinent_loggers : list of str, optional
        List of logger names that are relevant.
        Defaults to what is being tested in this module - the IPythonLogger
        logger instance.
    """
    with pytest.raises(Empty):
        next_pertinent_log_record(
            queue, pertinent_loggers=pertinent_loggers
        )


@pytest.mark.timeout(5)
def test_basic(ipylog, log_queue):
    logger.info("Sanity check: ensuring the queue handler works")
    ipython_logger.debug('hello')
    assert 'hello' in next_pertinent_log_record(log_queue).getMessage()
    logger.info("Log message recorded by handler: great!")
    assert_no_more_messages(log_queue)


@pytest.mark.timeout(5)
def test_one_in_no_output(ipylog, log_queue, fake_ipython):
    logger.info("One logged In, no output")
    fake_ipython.add_line('print(5)')
    assert 'In  [1]: print(5)' in next_pertinent_log_message(log_queue)
    assert_no_more_messages(log_queue)


@pytest.mark.timeout(5)
def test_one_in_one_out(ipylog, log_queue, fake_ipython):
    logger.info("One logged In, one Out")
    fake_ipython.add_line('1 + 1', 2)
    assert 'In  [1]: 1 + 1' in next_pertinent_log_message(log_queue)
    assert 'Out [1]: 2' in next_pertinent_log_message(log_queue)
    assert_no_more_messages(log_queue)


@pytest.mark.timeout(5)
def test_zero_division(ipylog, log_queue, fake_ipython):
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
    assert 'In  [1]: 1/0' in next_pertinent_log_message(log_queue)
    assert "Exception details" in next_pertinent_log_message(log_queue)


@pytest.mark.timeout(5)
def test_forced_failure(ipylog, log_queue, fake_ipython):
    logger.info("OK, now forcing a failure by tweaking internals")
    ipylog.ipython_in = None
    fake_ipython.add_line('something')
    assert 'Logging error' in next_pertinent_log_message(log_queue)
