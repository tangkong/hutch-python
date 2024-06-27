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
    curr_time: float
        The current time in seconds.

    max_idle_time: int
        The maximum number of seconds a user session can be idle (currently set
        to 172800 seconds or 48 hours).

    last_active_time: float
        The time of the last user activity in this session.

    idle_time: float
        The amount of time the user session has been idle.
    '''

    def __init__(self, ipython):
        global max_idle_time
        self.curr_time = 0
        self.max_idle_time = 30  # max_idle_time
        self.last_active_time = 0
        self.idle_time = 0
        self.user_active = False

        ipython.events.register('pre_run_cell', self._set_user_active)
        ipython.events.register('post_run_cell', self._set_user_inactive)

    def _set_user_active(self):
        self.user_active = True
        self.last_active_time = time.time()
        print("pre_cell_run")

    def _set_user_inactive(self):
        self.user_active = False
        self.last_active_time = time.time()
        print("post_cell_run")

    def _get_time_passed(self):
        self.curr_time = time.time()
        self.idle_time = self.curr_time - self.last_active_time

    def _timer(self, sleep_time):
        time.sleep(sleep_time)

    def _start_session(self):
        # Check if idle_time has exceeded max_idle_time
        while (self.idle_time < self.max_idle_time):

            while (self.user_active):
                time.sleep(6)
                self.idle_time = 0

            self._timer(self.max_idle_time - self.idle_time)
            self._get_time_passed()

        # Close the ipython session
        print("This hutch-python session has timed out. Please start a new session.")

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
