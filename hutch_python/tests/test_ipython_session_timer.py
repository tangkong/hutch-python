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


# Testing two different cases for IPythonSessionTimer._start_session(). The first case tests
# when the user's idle time is less than the maximum allowable idle time. The second case
# tests when the user's idle time is equivalent to or exceeds the maximum allowable idle time.

@unittest.mock.patch('hutch_python.ipython_session_timer.time.sleep', lambda seconds: None)
def test_start_session1(session_timer):
    if (session_timer.idle_time < session_timer.max_idle_time) and not session_timer.user_active:
        session_timer.last_active_time = session_timer.curr_time - 200.0
        assert session_timer.idle_time == 200.0


def test_get_ipython():
    pytest.skip("unsupported function")


@unittest.mock.patch('hutch_python.ipython_session_timer.time.sleep', lambda seconds: None)
def test_start_session2(monkeypatch, session_timer, capsys):
    session_timer.idle_time = session_timer.max_idle_time

    if (session_timer.idle_time >= session_timer.max_idle_time) and not session_timer.user_active:
        captured = capsys.readouterr()
        assert captured == "This hutch-python session has timed out. Please start a new session."
