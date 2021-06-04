import logging
from logging.handlers import QueueHandler
from pathlib import Path

import ophyd
import pytest
from conftest import restore_logging

from hutch_python import log_setup
from hutch_python.log_setup import (configure_log_directory, debug_context,
                                    debug_mode, debug_wrapper,
                                    get_console_handler, get_console_level,
                                    get_console_level_name, get_debug_handler,
                                    get_session_logfiles, log_objects,
                                    log_objects_off, set_console_level,
                                    setup_logging)

logger = logging.getLogger(__name__)


def test_setup_logging():
    logger.debug('test_setup_logging')
    dir_logs = Path(__file__).parent / 'logs'

    with restore_logging():
        setup_logging()

    with restore_logging():
        configure_log_directory(dir_logs)
        setup_logging()

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
        configure_log_directory(Path(__file__).parent / 'logs')
        setup_logging()
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
    return queue_handler


def clear(queue):
    items = []
    while not queue.empty():
        items.append(queue.get(block=False))
    return items


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
    assert get_console_level() == logging.DEBUG
    assert get_console_level_name() == "DEBUG"
    assert_is_debug(log_queue)

    set_console_level("INFO")
    assert get_console_level() == logging.INFO
    assert get_console_level_name() == "INFO"


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


def test_log_objects(monkeypatch, log_queue):
    filter = log_setup.ObjectFilter()

    def find_filters():
        yield handler, filter

    handler = setup_queue_console()
    handler.addFilter(filter)

    monkeypatch.setattr(log_setup, "find_root_object_filters",
                        find_filters)

    assert_is_info(log_queue)
    obj = ophyd.ophydobj.OphydObject(name="obj")
    ignored_obj = ophyd.ophydobj.OphydObject(name="ignored_obj")

    # Log messages prior to configuring it
    obj.log.debug("hidden-message-1")
    ignored_obj.log.debug("hidden-message-2")

    # Set the level so we see DEBUG messages in general
    set_console_level("DEBUG")
    # These still should be hidden - we ignore ophyd debug stream in general
    obj.log.info("hidden-message-3")
    ignored_obj.log.info("hidden-message-4")
    obj.log.info("hidden-message-5")
    ignored_obj.log.info("hidden-message-6")

    log_objects(obj, level="DEBUG")
    obj.log.info("shown-message-1")
    obj.log.debug("shown-message-2")

    ignored_obj.log.debug("hidden-message-7")
    ignored_obj.log.info("hidden-message-8")

    log_objects_off()
    obj.log.debug("hidden-message-9")
    obj.log.debug("hidden-message-10")
    messages = [
        msg.getMessage() for msg in clear(log_queue)
    ]
    assert set(messages) == {
        "Recording log messages from obj (level >=DEBUG)",
        "shown-message-1",
        "shown-message-2",
        "No longer recording log messages from obj",
    }
