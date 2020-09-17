"""
This module modifies an ``ipython`` shell to log inputs, outputs, and
tracebacks to a custom ``logger.input`` level. The ``INPUT`` level is lower
than the ``DEBUG`` level to avoid a terminal echo in debug mode.
"""
import functools
import logging
import sys
import traceback

from .constants import INPUT_LEVEL
from .log_setup import log_exception_to_central_server

logger = logging.getLogger(__name__)
logger.input = functools.partial(logger.log, INPUT_LEVEL)


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
        self.prev_err = None
        self.In = ipython.user_ns['In']
        self.Out = ipython.user_ns['Out']

    def log(self):
        """
        Logs the most recent inputs, outputs and exceptions.

        - Always logs the most recent input
        - If this input has a corresponding output, log the output
        - If there has been an error in the interactive session since the last
          call to `log`, log the error
        """
        try:
            line_num = len(self.In) - 1
            if line_num == 0:
                return
            last_in = self.In[-1]
            logger.input('In  [{}]: {}'.format(line_num, last_in))
            try:
                last_out = self.Out[line_num]
                # Convert to string, limit to max tweet length
                last_out = str(last_out)[:280]
                logger.input('Out [{}]: {}'.format(line_num, last_out))
            except KeyError:
                pass
            if hasattr(sys, 'last_value') and sys.last_value != self.prev_err:
                exc_info = (sys.last_type, sys.last_value, sys.last_traceback)
                logger.input(
                    'Exception in IPython session, traceback:\n%s',
                    ''.join(traceback.format_exception(*exc_info))
                )
                log_exception_to_central_server(exc_info)
                self.prev_err = sys.last_value
        except Exception:
            logger.input('Logging error', exc_info=True)


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
    logging.addLevelName('INPUT', INPUT_LEVEL)
    ipython.events.register('post_execute', IPythonLogger(ipython).log)
