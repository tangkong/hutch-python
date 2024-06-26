"""
This module modifies an ``ipython`` shell to automatically close if it has been
idle for 48 hours. Prior to starting hutch-python the user is alerted that the
shell will automatically close after another 24 hours and is given the option
to enter the number of hours they want to extend the session.
"""

import time
from threading import Thread

from IPython import get_ipython

max_idle_time = 172800  # number of seconds in 48 hours


def configure_timeout(session_timer):
    global max_idle_time
    if isinstance(session_timer, int) and session_timer > 0:
        max_idle_time = session_timer


class IPythonSessionTimer:
    '''
    Class tracks the amount of time the current `InteractiveShell` instance (henceforth
    called 'user session') has been idle and closes the session if more than 48
    hours have passed.

    Time is in seconds (floating point) since the epoch began. (In UNIX the
    epoch started on January 1, 1970, 00:00:00 UTC)

    Parameters
    ----------
    ipython : ``IPython.terminal.interactiveshell.TerminalInteractiveShell``
        The active ``ipython`` ``Shell``, perhaps the one returned by
        ``IPython.get_ipython()``.

    Attributes
    ----------
    max_idle_time: int
        The maximum number of seconds a user session can be idle (currently set
        to 172800 seconds or 48 hours).
    '''

    def __init__(self, ipython):
        global max_idle_time
        self.max_idle_time = max_idle_time
        self.user_active = False

        # _set_last_active_time() function will trigger every time user runs a cell
        ipython.events.register('pre_run_cell', self._set_user_active)
        ipython.events.register('post_run_cell', self._set_user_inactive)

    def _set_user_active(self, result):
        self.user_active = True

    def _set_user_inactive(self, result):
        self.user_active = False

    def _start_session(self):
        # poll for user activity
        while (1):
            if self.user_active == False:
                time.sleep(self.max_idle_time)
                if self.user_active == False:
                    break
            else:
                # check if the user has become inactive once every minute
                time.sleep(60)

        # Close the user session
        print("This hutch-python session has timed out and automatically closed. Please start a new session")

        # Close this ipython session
        ip = get_ipython()
        ip.ask_exit()
        ip.pt_app.app.exit()


def load_ipython_extension(ipython):
    """
    Initialize the `IPythonSessionTimer`.

    This starts a timer that checks if the user session has been
    idle for 48 hours or longer. If so, close the user session.

    Parameters
    ----------
    ipython: IPython.terminal.interactiveshell.TerminalInteractiveShell
        The active ``ipython`` ``Shell``, the one returned by
        ``IPython.get_ipython()``.
    """
    UserSessionTimer = IPythonSessionTimer(ipython)
    t1 = Thread(target=UserSessionTimer._start_session, daemon=True)
    t1.start()
