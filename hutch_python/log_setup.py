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
* By way of ``pcdsutils.log.install_log_warning_handler``, log all calls to
  ``warnings.warn`` at WARNING level

console exceptions:

* ophydobject INFO should be treated as DEBUG
* loggers which exceed the configurable log rate thresholds should be
  filtered out with an accompanying initial notification
* repeat warning logs and all callback exception logs should be treated as
  DEBUG instead of as WARNING and ERROR respectively

Hush entirely - neither the file nor the console should see:
  - ophyd.event_dispatcher
  - parso
  - pyPDB.dbd.yacc
"""
import collections
import logging
import logging.config
import os
import textwrap
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Iterable, Optional, TypeVar, Union

import coloredlogs
import ophyd
import pcdsutils.log
import yaml
from pcdsutils.log import (LogWarningLevelFilter,
                           OphydCallbackExceptionDemoter, validate_log_level)

from . import constants
from .utils import get_fully_qualified_domain_name

logger = logging.getLogger(__name__)
central_logger = pcdsutils.log.logger
LOG_DIR = None
OBJECT_NAME_STANDIN = "-"


class LoggingNotConfiguredError(Exception):
    ...


class DefaultFormatter(logging.Formatter):
    """
    A small ``logging.Formatter`` class to patch in a default
    'ophyd_object_name' as needed to logging records.
    """

    def format(self, record):
        record.__dict__.setdefault("ophyd_object_name", OBJECT_NAME_STANDIN)
        return super().format(record)


class ColoredFormatter(coloredlogs.ColoredFormatter):
    """The ``coloredlogs`` version of ``DefaultFormatter``, above."""

    def format(self, record):
        record.__dict__.setdefault("ophyd_object_name", OBJECT_NAME_STANDIN)
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
    with open(constants.FILE_YAML) as f:
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


def setup_logging() -> None:
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

    # Configure the warning redirect
    pcdsutils.log.install_log_warning_handler()

    logging.config.dictConfig(config)
    noisy_loggers = ['ophyd.event_dispatcher', 'parso',
                     'pyPDB.dbd.yacc', 'bluesky']
    hush_noisy_loggers(noisy_loggers)


FilterType = TypeVar('FilterType')


def find_root_filters(
    cls: type[FilterType],
) -> Generator[tuple[logging.Handler, FilterType], None, None]:
    """
    Find all filters of a given class configured on the root logger.

    This is useful as we configure the filters in ``logging.yaml``.

    Parameters
    ----------
    cls: type
        The logging.Filter subclass to search for.

    Yields
    ------
    handler : logging.Handler
    filter : cls
        This will always be an instance of the input cls type.
    """
    for handler in logging.root.handlers:
        for filter in handler.filters:
            if isinstance(filter, cls):
                yield handler, filter


def find_root_warning_filters() -> Generator[
    tuple[logging.Handler, LogWarningLevelFilter], None, None
]:
    """
    Find all ``LogWarningLevelFilter``s configured on the root logger.

    This is useful as we configure the filters in ``logging.yaml``.

    Yields
    ------
    handler : logging.Handler
    filter : pcdsutils.log.LogWarningLevelFilter
    """
    yield from find_root_filters(LogWarningLevelFilter)


def find_root_callback_filters() -> Generator[
    tuple[logging.Handler, OphydCallbackExceptionDemoter], None, None
]:
    """
    Find all ``OphydCallbackExceptionDemoter``s configured on the root logger.

    This is useful as we configure the filters in ``logging.yaml``.

    Yields
    ------
    handler : logging.Handler
    filter : pcdsutils.log.OphydCallbackExceptionDemoter
    """
    yield from find_root_filters(OphydCallbackExceptionDemoter)


class ObjectFilter(logging.Filter):
    """
    A logging filter that limits log messages to a specific object or objects.

    To be paired with a logging handler added to the ophyd object logger.

    Additionally has the capability of filtering out noisy loggers based on
    three thresholds: log message rates at 1 second, 10 seconds, and 60
    seconds.

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

    noisy_threshold_1s : int, optional
        If a single ophyd object logs over ``noisy_threshold_1s`` log messages
        in one second, consider it a noisy logger and silence it.  May be
        disabled by setting to 0.

    noisy_threshold_10s : int, optional
        If a single ophyd object logs over ``noisy_threshold_10s`` log messages
        in ten seconds, consider it a noisy logger and silence it.  May be
        disabled by setting to 0.

    noisy_threshold_60s : int, optional
        If a single ophyd object logs over ``noisy_threshold_60s`` log messages
        in 60 seconds, consider it a noisy logger and silence it.  May be
        disabled by setting to 0.

    whitelist : list of str, optional
        Logger or object names that are not subject to the thresholds above.

    blacklist : list of str, optional
        Logger or object names that should always be filtered out.

    Attributes
    ----------
    blacklist : list of str
        Logger names that should always be filtered out.

    whitelist : list of str
        List of noisy loggers or object names that are exempt from the noise
        thresholds.

    noisy_loggers: set of str
        Loggers marked as noisy and to be filtered out, unless in the
        whitelist.
    """
    _objects: frozenset[ophyd.ophydobj.OphydObject]
    _timer: threading.Thread
    _running: bool
    level: str
    allow_other_messages: bool
    whitelist_all_level: str
    name_to_log_count_1s: dict[str, int]
    name_to_log_count_10s: dict[str, int]
    name_to_log_count_60s: dict[str, int]
    noisy_threshold_1s: int
    noisy_threshold_10s: int
    noisy_threshold_60s: int
    whitelist: list[str]
    noisy_loggers: dict[str, int]
    blacklist: list[str]

    def __init__(
        self,
        *objects: ophyd.ophydobj.OphydObject,
        level: str = "WARNING",
        whitelist_all_level: str = "WARNING",
        noisy_threshold_1s: int = 20,
        noisy_threshold_10s: int = 50,
        noisy_threshold_60s: int = 100,
        whitelist: Optional[list[str]] = None,
        blacklist: Optional[list[str]] = None,
        allow_other_messages: bool = True
    ):
        self._objects = frozenset(objects)
        self.allow_other_messages = bool(allow_other_messages)
        self.whitelist_all_level = whitelist_all_level
        self.level = level
        self.name_to_log_count_1s = collections.defaultdict(int)
        self.name_to_log_count_10s = collections.defaultdict(int)
        self.name_to_log_count_60s = collections.defaultdict(int)
        self.noisy_threshold_1s = int(noisy_threshold_1s)
        self.noisy_threshold_10s = int(noisy_threshold_10s)
        self.noisy_threshold_60s = int(noisy_threshold_10s)
        self.whitelist = list(whitelist or [])
        self.blacklist = list(blacklist or [])
        self.noisy_loggers = {}

        self._running = True
        self._timer_index = 0

        self._timer = threading.Thread(target=self._count_update_thread)
        self._timer.daemon = True
        self._timer.start()

    def _count_update_thread(self) -> None:
        """Thread for checking the per-logger statistics."""
        while self._running:
            self._count_update()
            time.sleep(1.0)

    def _count_update(self) -> None:
        """Log count update - every second."""
        noisy_loggers = {
            name
            for name, count in tuple(self.name_to_log_count_1s.items())
            if count > self.noisy_threshold_1s > 0
        } | {
            name
            for name, count in tuple(self.name_to_log_count_10s.items())
            if count > self.noisy_threshold_10s > 0
        } | {
            name
            for name, count in tuple(self.name_to_log_count_60s.items())
            if count > self.noisy_threshold_60s > 0
        }

        for noisy_logger in sorted(noisy_loggers):
            if noisy_logger in self.whitelist:
                continue
            if noisy_logger in self.noisy_loggers:
                continue

            logger.info(
                "Hushing noisy logger %r. If you see this often, please "
                "consider reporting it to your POC or #pcds-help.  If this "
                "functionality is undesirable, adjust the thresholds or set "
                "`logs.filter.whitelist`.",
                noisy_logger
            )
            self.noisy_loggers.setdefault(noisy_logger, 0)

        self._timer_index = (self._timer_index + 1) % 60
        if self._timer_index == 0:
            self.name_to_log_count_60s.clear()
        if (self._timer_index % 10) == 0:
            self.name_to_log_count_10s.clear()
        self.name_to_log_count_1s.clear()

    def stop(self) -> None:
        """Stop updating logging rates in the background."""
        self._running = False

    def __del__(self) -> None:
        try:
            self.stop()
        except Exception:
            # Teardown of interpreter may cause attributeerrors and more.
            ...

    def __repr__(self) -> str:
        objects = ", ".join(obj.name for obj in self.objects)
        return (
            f"{self.__class__.__name__}("
            f"level={self.level}, "
            f"allow_other_messages={self.allow_other_messages}, "
            f"objects=[{objects}], "
            f"noisy_threshold_1s={self.noisy_threshold_1s}, "
            f"noisy_threshold_10s={self.noisy_threshold_10s}, "
            f"noisy_threshold_60s={self.noisy_threshold_60s}, "
            f"whitelist={self.whitelist}, "
            f"noisy_loggers={self.noisy_loggers}"
            f")"
        )

    def _repr_pretty_(self, pp, cycle: bool) -> str:
        """
        IPython pretty-printing to show current status information.

        Parameters
        ----------
        pp : PrettyPrinter
            An instance of PrettyPrinter is always passed into the method.
            This is what you use to determine what gets printed.
            pp.text('text') adds non-breaking text to the output.
            pp.breakable() either adds a whitespace or breaks here.
            pp.pretty(obj) pretty prints another object.
            with pp.group(4, 'text', 'text') groups items into an intended set
            on multiple lines.

        cycle : bool
            This is True when the pretty printer detects a cycle, e.g. to help
            you avoid infinite loops. For example, your _repr_pretty_ method
            may call pp.pretty to print a sub-object, and that object might
            also call pp.pretty to print this object. Then cycle would be True
            and you know not to make any further recursive calls.
        """
        pp.text(self.description)

    @property
    def description(self) -> str:
        """A description of the current configuration."""
        objects = [obj.name for obj in self.objects]
        noisy_loggers = ("\n" + 14 * " ").join(
            f"{logger!r}: {count} messages"
            for logger, count in self.noisy_loggers.items()
        )
        return textwrap.dedent(
            f"""\
            Objects
            -------
            * Allow log messages at level: {self.level}
            * Show messages from objects: {objects}

            Loggers
            -------
            * Block these loggers/objects entirely: {self.blacklist}
            * Allow these noisy loggers/objects: {self.whitelist}
            * Hush loggers with {self.noisy_threshold_1s} messages in 1s
            * Hush loggers with {self.noisy_threshold_10s} messages in 10s
            * Hush loggers with {self.noisy_threshold_60s} messages in 60s
            * These loggers have been identified as noisy:
              {noisy_loggers}

            Usage
            -----
            * To allow a noisy logger or ophyd device through:
                >>> logs.filter.whitelist.append('logger_name')
            * To always filter out a logger or ophyd device:
                >>> logs.filter.blacklist.append('logger_name')
            * To focus on specific ophyd objects:
                >>> logs.log_objects(obj1, obj2)
            * To stop
                >>> logs.log_objects_off()
            """.rstrip()
        )

    def disable(self) -> None:
        """Disable the filter."""
        self.objects = []
        self.allow_other_messages = True

    @property
    def objects(self) -> list[ophyd.ophydobj.OphydObject]:
        """The objects to log."""
        return list(sorted(self._objects, key=lambda obj: obj.name))

    @objects.setter
    def objects(self, objects: Iterable[ophyd.ophydobj.OphydObject]) -> None:
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
    def level(self, value: Union[int, str]) -> None:
        self._levelno = validate_log_level(value)

    @property
    def whitelist_all_level(self) -> str:
        """The logging level at which we whitelist *all* objects."""
        return logging.getLevelName(self._whitelist_all_levelno)

    @whitelist_all_level.setter
    def whitelist_all_level(self, value: Union[int, str]):
        self._whitelist_all_levelno = validate_log_level(value)

    @property
    def object_names(self) -> set[str]:
        """The names of all contained objects."""
        return {obj.name for obj in self.objects}

    def filter(self, record: logging.LogRecord) -> bool:
        name: Optional[str] = getattr(record, "ophyd_object_name", None)
        if name is None or name == OBJECT_NAME_STANDIN:
            should_show = (
                self.allow_other_messages and
                name not in self.blacklist
            )
            name = record.name
        else:
            if record.levelno == logging.INFO:
                # This is rather dastardly, but we consider ophydobj INFO to be
                # closer to DEBUG.  Make it so.
                record.levelno = logging.DEBUG
                record.levelname = "DEBUG"

            should_show = (
                record.levelno >= self._whitelist_all_levelno or
                name in self.object_names
            ) and name not in self.blacklist

        is_noisy = (
            name in self.noisy_loggers and
            name not in self.whitelist and
            name not in self.object_names
        )

        if should_show:
            self.name_to_log_count_1s[name] += 1
            self.name_to_log_count_10s[name] += 1
            self.name_to_log_count_60s[name] += 1

        if is_noisy:
            # Avoid using += here in case `noisy_loggers` gets cleared.
            self.noisy_loggers[name] = self.noisy_loggers.get(name, 0) + 1

        return should_show and not is_noisy


def find_root_object_filters() -> Generator[
    tuple[logging.Handler, ObjectFilter], None, None
]:
    """
    Find all ``ObjectFilter``s configured on the root logger.

    This is useful as we configure the filters in ``logging.yaml``.

    Yields
    ------
    handler : logging.Handler
    filter : ObjectFilter
    """
    yield from find_root_filters(ObjectFilter)


def get_object_filter(name: str) -> Optional[ObjectFilter]:
    """
    Get a specific object filter instance, if available.

    Parameters
    ----------
    name : str
        The root logger handler name - {"console", "debug"}.
        See ``logging.yml`` for more information.
    """
    try:
        handler = get_handler(name)
    except RuntimeError:
        ...
    else:
        filters = [
            flt for flt in handler.filters
            if isinstance(flt, ObjectFilter)
        ]
        if filters:
            return filters[0]
    return None


def log_objects_off() -> None:
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
    raise RuntimeError(f'No {name} handler')


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
    kwargs = dict(stacklevel=stacklevel + 1)

    central_logger.log(level, message, exc_info=exc_info, **kwargs)
