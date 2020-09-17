import logging
from logging.handlers import QueueHandler
from pathlib import Path

import pytest
from conftest import restore_logging

from hutch_python.log_setup import (debug_context, debug_mode, debug_wrapper,
                                    get_console_handler, get_debug_handler,
                                    get_session_logfiles, set_console_level,
                                    setup_logging)

logger = logging.getLogger(__name__)


def test_setup_logging():
    logger.debug('test_setup_logging')
    dir_logs = Path(__file__).parent / 'logs'

    with restore_logging():
        setup_logging()

    with restore_logging():
        setup_logging(dir_logs=dir_logs)

    assert dir_logs.exists()


def test_console_handler(log_queue):
    logger.debug('test_console_handler')

    with pytest.raises(RuntimeError):
        handler = get_console_handler()

    with restore_logging():
        setup_queue_console()
        handler = get_console_handler()
        assert isinstance(handler, QueueHandler)


def test_get_session_logfiles():
    logger.debug('test_get_session_logfiles')
    with restore_logging():
        # Create a parent log file
        setup_logging(dir_logs=Path(__file__).parent / 'logs')
        debug_handler = get_debug_handler()
        debug_handler.doRollover()
        debug_handler.doRollover()
        assert len(get_session_logfiles()) == 3
        assert all([log.startswith(debug_handler.baseFilename)
                    for log in get_session_logfiles()])


def setup_queue_console():
    root_logger = logging.getLogger('')
    for handler in root_logger.handlers:
        if isinstance(handler, QueueHandler):
            queue_handler = handler
            break
    queue_handler.name = 'console'
    queue_handler.level = 20


def clear(queue):
    while not queue.empty():
        queue.get(block=False)


def assert_is_info(queue):
    clear(queue)
    logger.info('hello')
    logger.debug('goodbye')
    assert 'hello' in queue.get(block=False).getMessage()
    assert queue.empty()


def assert_is_debug(queue):
    clear(queue)
    logger.debug('goodbye')
    assert 'goodbye' in queue.get(block=False).getMessage()


def test_set_console_level(log_queue):
    logger.debug('test_set_console_level')

    setup_queue_console()
    assert_is_info(log_queue)

    # Change console level so we get debug statements
    set_console_level(logging.DEBUG)
    assert_is_debug(log_queue)


def test_debug_mode(log_queue):
    logger.debug('test_debug_mode')

    setup_queue_console()
    assert not debug_mode()
    assert_is_info(log_queue)

    debug_mode(debug=True)
    assert debug_mode()
    assert_is_debug(log_queue)

    debug_mode(debug=False)
    assert not debug_mode()
    assert_is_info(log_queue)


def test_debug_context(log_queue):
    logger.debug('test_debug_context')

    setup_queue_console()
    assert_is_info(log_queue)

    with debug_context():
        assert_is_debug(log_queue)

    assert_is_info(log_queue)


def test_debug_wrapper(log_queue):
    logger.debug('test_debug_wrapper')

    setup_queue_console()
    assert_is_info(log_queue)

    debug_wrapper(assert_is_debug, log_queue)

    assert_is_info(log_queue)
