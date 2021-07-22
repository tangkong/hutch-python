"""
This module is used to set up and manipulate the ``logging`` configuration for
utilities like debug mode.

Functionality overview
======================

By way of :class:`hutch_python.ipython_log.IPythonLogger`, log the following
to ``{{LOG_DIR}}/year_month/user_timestamp.log``:

* All IPython input
* Any DEBUG message (well, _level 5+_)
  - Exception: hushed loggers, listed below
  - Exception: Only whitelisted ophyd object logs, down to DEBUG level (or 5)

Log to both the above file and console:
* Any INFO, WARNING, ERROR, CRITICAL messages

console exceptions:
* ophydobject INFO should be treated as DEBUG

Hush entirely - neither the file nor the console should see:
  - ophyd.event_dispatcher
  - parso
  - pyPDB.dbd.yacc
"""
import logging
import logging.config
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Union

import coloredlogs
import pcdsutils.log
import yaml

from . import constants
from .utils import get_fully_qualified_domain_name

logger = logging.getLogger(__name__)
central_logger = pcdsutils.log.logger
LOG_DIR = None


class LoggingNotConfiguredError(Exception):
    ...


class DefaultFormatter(logging.Formatter):
    """
    A small ``logging.Formatter`` class to patch in a default
    'ophyd_object_name' as needed to logging records.
    """

    def format(self, record):
        record.__dict__.setdefault("ophyd_object_name", "-")
        return super().format(record)


class ColoredFormatter(coloredlogs.ColoredFormatter):
    """The ``coloredlogs`` version of ``DefaultFormatter``, above."""

    def format(self, record):
        record.__dict__.setdefault("ophyd_object_name", "-")
        return super().format(record)


def get_log_filename(extension: str = '.log') -> Path:
    """
    Get a logger filename and ready it for usage.

    Parameters
    ----------
    extension : str
        The log file extension.

    Returns
    -------
    pathlib.Path :
        The log file path.
    """
    if LOG_DIR is None:
        raise LoggingNotConfiguredError(
            "Logging was not configured (LOG_DIR unset).  If in production "
            "mode, please call `configure_log_directory` first."
        )

    # Subdirectory for year/month
    dir_month = LOG_DIR / time.strftime('%Y_%m')

    # Make the log directories if they don't exist
    # Make sure each level is all permissions
    for directory in (LOG_DIR, dir_month):
        if not directory.exists():
            directory.mkdir()
            directory.chmod(0o777)

    user = os.environ['USER']
    timestamp = time.strftime('%d_%Hh%Mm%Ss')

    logfile = dir_month / f'{user}_{timestamp}{extension}'
    logfile.touch()
    return logfile


def _read_logging_config() -> dict:
    """Read the logging configuration file into a dictionary."""
    with open(constants.FILE_YAML, 'rt') as f:
        return yaml.safe_load(f.read())


def get_log_directory() -> Optional[Path]:
    """Get the currently configured logging path."""
    return LOG_DIR


def configure_log_directory(dir_logs: Optional[Union[str, Path]]):
    """
    Configure the logging path.

    Parameters
    ----------
    dir_logs: ``str`` or ``Path``, optional
        Path to the log directory. If omitted, we won't use a log file.
    """
    global LOG_DIR
    LOG_DIR = Path(dir_logs).expanduser().resolve() if dir_logs else None


def setup_logging():
    """
    Sets up the ``logging`` configuration.

    Uses ``logging.yml`` to define the config
    and manages the ``log`` directory paths.

    Also sets up the standard pcds logstash handler.
    """
    config = _read_logging_config()

    if LOG_DIR is None:
        # Remove debug file from the config
        del config['handlers']['debug']
        config['root']['handlers'].remove('debug')
    else:
        config['handlers']['debug']['filename'] = str(get_log_filename())

    # Configure centralized PCDS logging:
    fqdn = get_fully_qualified_domain_name()
    if any(fqdn.endswith(domain) for domain in constants.LOG_DOMAINS):
        pcdsutils.log.configure_pcds_logging()

    # This ensures that centralized logging messages do not make it to the
    # user or other log files.
    central_logger.propagate = False

    logging.config.dictConfig(config)
    noisy_loggers = ['ophyd.event_dispatcher', 'parso',
                     'pyPDB.dbd.yacc', 'bluesky']
    hush_noisy_loggers(noisy_loggers)


def validate_log_level(level: Union[str, int]) -> int:
    '''
    Return a logging level integer for level comparison.

    Parameters
    ----------
    level : str or int
        The logging level string or integer value.

    Returns
    -------
    log_level : int
        The integral log level.

    Raises
    ------
    ValueError
        If the logging level is invalid.
    '''
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        levelno = logging.getLevelName(level)

    if not isinstance(levelno, int):
        raise ValueError("Invalid logging level (use e.g., DEBUG or 6)")

    return levelno


class ObjectFilter(logging.Filter):
    '''
    A logging filter that limits log messages to a specific object or objects.

    To be paired with a logging handler added to the ophyd object logger.

    Parameters
    ----------
    objs : iterable of OphydObject
        Ophyd objects to filter.

    level : str or int
        Cut-off level for log messages.
        Default is 'WARNING'. Python log level names or their corresponding
        integers are accepted.

    whitelist_all_level : str or int
        Cut-off level for log messages.
        Default is 'WARNING'. Python log level names or their corresponding
        integers are accepted.

    allow_other_messages : bool, optional
        Allow messages through the filter that are not specific to ophyd
        objects.  Ophyd object-related messages _must_ pass the filter.
    '''
    def __init__(self, *objects, level='WARNING',
                 whitelist_all_level='WARNING', allow_other_messages=True):
        self._objects = frozenset(objects)
        self.allow_other_messages = bool(allow_other_messages)
        self.whitelist_all_level = whitelist_all_level
        self.level = level

    def __repr__(self):
        objects = ", ".join(obj.name for obj in self.objects)
        return (
            f"{self.__class__.__name__}("
            f"level={self.level}, "
            f"allow_other_messages={self.allow_other_messages}, "
            f"objects=[{objects}]"
            f")"
        )

    def disable(self):
        """Disable the filter."""
        self.objects = []
        self.allow_other_messages = True

    @property
    def objects(self):
        """The objects to log."""
        return list(sorted(self._objects, key=lambda obj: obj.name))

    @objects.setter
    def objects(self, objects):
        self._objects = frozenset(objects)

    @property
    def levelno(self) -> int:
        """The logging level number."""
        return self._levelno

    @property
    def level(self) -> str:
        """The logging level name."""
        return logging.getLevelName(self._levelno)

    @level.setter
    def level(self, value):
        self._levelno = validate_log_level(value)

    @property
    def whitelist_all_level(self) -> str:
        """The logging level at which we whitelist *all* objects."""
        return logging.getLevelName(self._whitelist_all_levelno)

    @whitelist_all_level.setter
    def whitelist_all_level(self, value):
        self._whitelist_all_levelno = validate_log_level(value)

    @property
    def object_names(self):
        """The names of all contained objects."""
        return set(obj.name for obj in self.objects)

    def filter(self, record):
        if not hasattr(record, 'ophyd_object_name'):
            return self.allow_other_messages

        if record.levelno == logging.INFO:
            # This is rather dastardly, but we consider ophydobj INFO to be
            # closer to DEBUG.  Make it so.
            record.levelno = logging.DEBUG
            record.levelname = "DEBUG"

        if record.levelno >= self._whitelist_all_levelno:
            return True

        # if record.levelno < self.levelno:
        #     return self.allow_other_messages

        return record.ophyd_object_name in self.object_names


def find_root_object_filters():
    """
    Find all ``ObjectFilter``s configured on the root logger.

    This is useful as we configure the filters in ``logging.yaml``.

    Yields
    ------
    handler : logging.Handler
    filter : ObjectFilter
    """
    for handler in logging.root.handlers:
        for filter in handler.filters:
            if isinstance(filter, ObjectFilter):
                yield handler, filter


def log_objects_off():
    """
    Return to default logging behavior and do not treat objects specially.
    """
    log_objects(level="WARNING", console=True)


def log_objects(
    *objects,
    level: str = "DEBUG",
    console: bool = True,
):
    """
    Configure a custom logging handler on the specified object(s), and record
    log messages to files and (optionally) to the console.

    Parameters
    ----------
    *objects :
        The ``OphydObject`` instances.

    level : str, optional
        The minimum logging level to allow.  Note that the console logger
        must still have its level set appropriately. The file logger should be
        OK as it has a low default level (5, below DEBUG).

    console : bool, optional
        Apply object logging to the console as well as the rotating log file.
    """
    notification_level = 0

    old_objects = set()
    for handler, filter in find_root_object_filters():
        if isinstance(handler, logging.StreamHandler) and not console:
            continue

        old_objects = old_objects.union(filter.objects)
        filter.objects = objects
        filter.level = level
        notification_level = max((notification_level, handler.level))

    for obj in objects:
        obj.log.log(
            notification_level,
            "Recording log messages from %s (level >=%s)",
            obj.name, level
        )

    for obj in old_objects.difference(objects):
        obj.log.warning(
            "No longer recording log messages from %s",
            obj.name
        )


def hush_noisy_loggers(modules, level=logging.WARNING):
    """
    Some loggers spam on INFO with no restraint, so we must raise their levels.

    It seems there is some disagreement over what log levels should mean. In
    our repos, INFO is used as the de-facto print replacement, but in some
    repos it is used as the secondary debug stream.
    """
    for module in modules:
        logging.getLogger(module).propagate = False


def get_session_logfiles():
    """
    Get the path to the current debug log file

    Returns
    -------
    logs : list
        List of absolute paths to log files that were created by this session.
        Returns an empty list if there is no ``RotatingFileHandler`` with the
        name ``debug``
    """
    # Grab the debug file handler
    try:
        handler = get_debug_handler()
    except RuntimeError:
        logger.warning("No debug RotatingFileHandler configured for session")
        return list()
    # Find all the log files that were generated by this session
    base = Path(handler.baseFilename)
    return [str(base.parent / log)
            for log in os.listdir(base.parent)
            if log.startswith(base.name)]


def get_console_handler():
    """
    Helper function to find the console ``StreamHandler``.

    Returns
    -------
    console: ``StreamHandler``
        The ``Handler`` that prints to the screen.
    """
    return get_handler('console')


def get_debug_handler():
    """
    Helper function to find the debug ``RotatingFileHandler``

    Returns
    -------
    debug: ``RotatingFileHandler``
        The ``Handler`` that prints to the log files
    """
    return get_handler('debug')


def get_handler(name):
    """
    Helper function to get an arbitrary `Handler`

    Returns
    -------
    hander : `Handler`
    """
    root = logging.getLogger('')
    for handler in root.handlers:
        if handler.name == name:
            return handler
    raise RuntimeError('No {} handler'.format(name))


def get_console_level():
    """
    Helper function to get the console's log level.

    Returns
    -------
    level: ``int``
        Compare to ``logging.INFO``, ``logging.DEBUG``, etc. to see which log
        messages will be printed to the screen.
    """
    handler = get_console_handler()
    return handler.level


def get_console_level_name():
    """
    Helper function to get the console's log level name.

    Returns
    -------
    level: str
        The current console log level as a user-friendly string.
    """
    return logging.getLevelName(get_console_level())


def set_console_level(level=logging.INFO):
    """
    Helper function to set the console's log level.

    Parameters
    ----------
    level: int or str
        Likely one of ``logging.INFO``, ``logging.DEBUG``, etc.
    """
    handler = get_console_handler()
    handler.level = validate_log_level(level)


def debug_mode(debug=None):
    """
    Enable, disable, or check if we're in debug mode.

    Debug mode means that the console's logging level is ``logging.DEBUG`` or
    lower, which means we'll see all of the internal log messages that usually
    are not sent to the screen.

    Parameters
    ----------
    debug: ``bool``, optional
        If provided, we'll turn debug mode on (``True``) or off (``False``)

    Returns
    -------
    debug: ``bool`` or ``None``
        Returned if `debug_mode` is called with no arguments. This is ``True`
        if we're in debug mode, and ``False`` otherwise.
    """
    if debug is None:
        level = get_console_level()
        return level <= logging.DEBUG
    elif debug:
        set_console_level(level=logging.DEBUG)
    else:
        set_console_level(level=logging.INFO)


@contextmanager
def debug_context():
    """
    Context manager for running a block of code in `debug_mode`.

    For example:

    .. code-block:: python

        with debug_context():
            buggy_function()
    """
    old_level = get_console_level()
    debug_mode(True)
    yield
    set_console_level(level=old_level)


def debug_wrapper(f, *args, **kwargs):
    """
    Wrapper for running a function in `debug_mode`.

    Parameters
    ----------
    f: ``function``
        Wrapped function to call

    *args:
        Function arguments

    **kwargs:
        Function keyword arguments
    """
    with debug_context():
        f(*args, **kwargs)


def log_exception_to_central_server(
    exc_info, *,
    context='exception',
    message=None,
    level=logging.ERROR,
    stacklevel=1,
):
    """
    Log an exception to the central server (i.e., logstash/grafana).

    Parameters
    ----------
    exc_info : (exc_type, exc_value, exc_traceback)
        The exception information.

    context : str, optional
        Additional context for the log message.

    message : str, optional
        Override the default log message.

    level : int, optional
        The log level to use.  Defaults to ERROR.

    stacklevel : int, optional
        The stack level of the message being reported.  Defaults to 1,
        meaning that the message will be reported as having come from
        the caller of ``log_exception_to_central_server``.  Applies
        only to Python 3.8+, and ignored below.
    """
    exc_type, exc_value, exc_traceback = exc_info
    if issubclass(exc_type, constants.NO_LOG_EXCEPTIONS):
        return

    if not central_logger.handlers:
        # Do not allow log messages unless the central logger has been
        # configured with a log handler.  Otherwise, the log message will
        # hit the default handler and output to the terminal.
        return

    message = message or f'[{context}] {exc_value}'
    kwargs = dict()
    if sys.version_info >= (3, 8):
        kwargs = dict(stacklevel=stacklevel + 1)

    central_logger.log(level, message, exc_info=exc_info, **kwargs)
