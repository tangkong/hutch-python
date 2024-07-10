import time
import unittest

import pytest
from test_ipython_log import FakeIPython

from hutch_python.ipython_session_timer import IPythonSessionTimer


@pytest.fixture(scope='function')
def fake_ipython():
    fake_ipython = FakeIPython()
    fake_ipython.ask_exit = lambda *args, **kwargs: None
    return fake_ipython


@pytest.fixture(scope='function')
def session_timer(fake_ipython):
    session_timer = IPythonSessionTimer(fake_ipython)
    session_timer.max_idle_time = 20.0
    session_timer.user_active = True
    session_timer.curr_time = time.monotonic()
    session_timer.last_active_time = session_timer.curr_time - 10.0
    session_timer.idle_time = session_timer.curr_time - session_timer.last_active_time
    return session_timer


def test_set_user_active(session_timer):
    assert session_timer.user_active


def test_set_user_inactive(session_timer):
    session_timer.user_active = False
    assert not session_timer.user_active


def test_set_idle_time(session_timer):
    assert session_timer.idle_time == 10.0


# Skipping tests for _start_session() where self.user_active==True because this enters an
# infinite while loop.

@unittest.mock.patch('time.sleep', lambda seconds: None)
def test_start_session(session_timer, fake_ipython, capsys):
    session_timer.user_active = False

    session_timer._start_session()

    captured = capsys.readouterr()
    assert "timed out" in captured.out
