"""
This module modifies an ``ipython`` shell to log inputs, outputs, and
tracebacks to a custom ``logger.input`` level. The ``INPUT`` level is lower
than the ``DEBUG`` level to avoid a terminal echo in debug mode.
"""
import functools
import logging
import sys
import textwrap
import traceback

from .constants import INPUT_LEVEL
from .log_setup import log_exception_to_central_server

logger = logging.getLogger(__name__)
logger.propagate = False
logger.setLevel(INPUT_LEVEL)
logger.input = functools.partial(logger.log, INPUT_LEVEL)
_ip_logger = None


def _log_errors(func):
    """Decorator: wrap ``func`` to log exceptions."""

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.input('Logging error', exc_info=True)
    return wrapped


_indented = functools.partial(textwrap.indent, prefix=' ' * 4)


class IPythonLogger:
    """
    Class that logs the most recent inputs, outputs, and exceptions at the
    custom ``INPUT`` level.

    Parameters
    ----------
    ipython: ``ipython`` ``Shell``
        The active ``ipython`` ``Shell``, perhaps the one returned by
        ``IPython.get_ipython()``.
    """
    def __init__(self, ipython):
        self.prev_err_value = None
        self.ipython = ipython
        self.info = None
        self.result = None
        self.ipython_in = ipython.user_ns["In"]
        ipython.events.register('pre_run_cell', self.log_user_input)
        ipython.events.register('post_run_cell', self.log_output)

    @_log_errors
    def log_user_input(self, info):
        """Logs the most recent input by way of the 'pre_run_cell' hook."""
        self.info = info
        line_num = len(self.ipython_in)
        logger.input('In  [%d]: %s', line_num, info.raw_cell)

    @_log_errors
    def log_exception(self, result):
        """Logs the most recent unhandled exception."""
        # These three ``sys.last_*`` variables are not always defined; they are
        # set when an exception is not handled and the interpreter prints an
        # error message and a stack traceback.

        last_value = getattr(sys, "last_value", None)
        if not last_value:
            # No exception to log
            return

        if last_value == self.prev_err_value:
            # Same as last time; ignore this
            logger.input(
                '[Repeated %s omitted]', sys.last_type,
            )
            return

        try:
            exc_info = (sys.last_type, last_value, sys.last_traceback)
            line_num = len(self.ipython_in) - 1
            line_input = result.info.raw_cell
            line_traceback = ''.join(traceback.format_exception(*exc_info))
            logger.input(
                f"""\
Exception in IPython session. Input on line {line_num}:
{_indented(line_input)}

Exception:
{_indented(line_traceback)}
""".rstrip()
            )

            log_exception_to_central_server(
                exc_info,
                message=f"""\
Line: {line_num}
Input: {line_input}
Exception: {sys.last_type.__name__}: {sys.last_value}
""".rstrip(),
            )
        finally:
            self.prev_err_value = last_value

    @_log_errors
    def log_output(self, result):
        """Logs the most recent output by way of the 'post_run_cell' hook."""
        self.result = result
        if result.result:
            # Convert to string, limit to max tweet length
            line_num = len(self.ipython_in) - 1
            last_out = str(result.result)[:280]
            logger.input('Out [%d]: %s', line_num, last_out)

        if result.error_in_exec is not None:
            self.log_exception(result)


def load_ipython_extension(ipython):
    """
    Initialize the `IPythonLogger`.

    This involves adding the ``INPUT`` log level and registering
    `IPythonLogger.log` to run on the ``post-execute`` event.

    Parameters
    ----------
    ip: ``ipython`` ``Shell``
        The active ``ipython`` ``Shell``, perhaps the one returned by
        ``IPython.get_ipython()``.
    """
    global _ip_logger
    logging.addLevelName('INPUT', INPUT_LEVEL)
    _ip_logger = IPythonLogger(ipython)
