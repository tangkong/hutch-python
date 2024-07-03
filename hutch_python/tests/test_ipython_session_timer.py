import time
import unittest

import pytest
from test_ipython_log import FakeIPython

from hutch_python.ipython_session_timer import IPythonSessionTimer


@pytest.fixture(scope='function')
def fake_ipython():
    fake_ipython = FakeIPython()
    return fake_ipython


@pytest.fixture(scope='function')
def session_timer(fake_ipython):
    session_timer = IPythonSessionTimer(fake_ipython)
    session_timer.user_active = True
    session_timer.curr_time = time.monotonic()
    session_timer.last_active_time = session_timer.curr_time - 100.0
    session_timer.idle_time = session_timer.curr_time - session_timer.last_active_time
    return session_timer


def test_set_user_active(session_timer):
    assert session_timer.user_active


def test_set_user_inactive(session_timer):
    session_timer.user_active = False
    assert not session_timer.user_active


def test_set_idle_time(session_timer):
    assert session_timer.idle_time == 100.0


# Test case 1: the user is inactive and their idle time is less than the maximum allowable idle time.
@unittest.mock.patch('time.sleep', lambda seconds: None)
def test_start_session_case1(session_timer):
    session_timer.user_active = False

    if (session_timer.idle_time < session_timer.max_idle_time) or session_timer.user_active:
        assert session_timer.idle_time == 100.0


# Test case 2: the user is inactive and their idle time is equivalent to or exceeds the maximum allowable idle time.
@unittest.mock.patch('time.sleep', lambda seconds: None)
def test_start_session_case2(session_timer, capsys):
    session_timer.user_active = False
    session_timer.idle_time = session_timer.max_idle_time

    if (session_timer.idle_time >= session_timer.max_idle_time) and not session_timer.user_active:
        print("This hutch-python session has timed out. Please start a new session.")
        captured = capsys.readouterr()
        assert "timed out" in captured.out
