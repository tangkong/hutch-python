import logging
import queue
import uuid
from logging.handlers import QueueHandler
from pathlib import Path

import ophyd
import pytest
from conftest import restore_logging
from pcdsutils.log import LogWarningLevelFilter, OphydCallbackExceptionDemoter

from hutch_python import log_setup
from hutch_python.log_setup import (ObjectFilter, configure_log_directory,
                                    debug_context, debug_mode, debug_wrapper,
                                    find_root_filters, get_console_handler,
                                    get_console_level, get_console_level_name,
                                    get_debug_handler, get_session_logfiles,
                                    log_objects, log_objects_off,
                                    set_console_level, setup_logging)

from .conftest import skip_if_win32_generic

logger = logging.getLogger(__name__)


@skip_if_win32_generic
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


@skip_if_win32_generic
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
    queue_handler.level = logging.INFO
    return queue_handler


def clear(queue):
    items = []
    while not queue.empty():
        items.append(queue.get(block=False))
    return items


def assert_is_info(queue):
    clear(queue)
    info_msg = str(uuid.uuid4())
    debug_msg = str(uuid.uuid4())
    logger.info(info_msg)
    logger.debug(debug_msg)
    messages = [rec.getMessage() for rec in clear(queue)]
    assert info_msg in messages
    assert debug_msg not in messages


def assert_is_debug(queue):
    clear(queue)
    debug_msg = str(uuid.uuid4())
    logger.debug(debug_msg)
    assert debug_msg in [rec.getMessage() for rec in clear(queue)]


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


@pytest.fixture(scope="function")
def object_filter(
    monkeypatch, log_queue: queue.Queue
) -> log_setup.ObjectFilter:
    def no_op(*args, **kwargs):
        ...

    monkeypatch.setattr(log_setup.ObjectFilter, "_count_update_thread", no_op)
    object_filter = log_setup.ObjectFilter()
    handler = setup_queue_console()
    handler.addFilter(object_filter)
    assert_is_info(log_queue)
    object_filter._count_update()
    return object_filter


def test_log_noisy(caplog, object_filter: log_setup.ObjectFilter):
    object_filter.noisy_threshold_1s = 5

    assert logger.name not in object_filter.noisy_loggers

    for i in range(10):
        logger.warning("Warning")

    assert object_filter.name_to_log_count_1s[logger.name] == 10

    caplog.clear()
    object_filter._count_update()
    assert "Hushing noisy logger" in caplog.text
    assert logger.name in caplog.text

    assert logger.name in object_filter.noisy_loggers


def test_log_noisy_whitelist(caplog, object_filter: log_setup.ObjectFilter):
    object_filter.noisy_threshold_1s = 5
    object_filter.whitelist = [logger.name]

    # Exceed the threshold of log messages
    for i in range(10):
        logger.warning("Warning")

    assert object_filter.name_to_log_count_1s[logger.name] == 10

    object_filter._count_update()

    # But the logger isn't considered noisy - as it's whitelisted
    assert logger.name not in object_filter.noisy_loggers
    logger.warning("This should be whitelisted")
    assert "This should be whitelisted" in caplog.text


@pytest.mark.parametrize(
    'filter_cls',
    (ObjectFilter, LogWarningLevelFilter, OphydCallbackExceptionDemoter),
)
def test_filter_installed(filter_cls):
    with restore_logging():
        setup_logging()
        filts = list(find_root_filters(filter_cls))
    assert filts, f"Did not find any {filter_cls.__name__} filters"
