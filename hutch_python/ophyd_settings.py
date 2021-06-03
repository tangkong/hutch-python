"""
Module to contain ophyd-specific settings that must be applied prior to
creating any ophyd objects.
"""
import os

from ophyd.signal import EpicsSignalBase

# Environment variable definitions
CONN_VAR = 'HUTCH_PYTHON_CONNECTION_TIMEOUT'
READ_VAR = 'HUTCH_PYTHON_READ_TIMEOUT'
WRITE_VAR = 'HUTCH_PYTHON_WRITE_TIMEOUT'
AUTO_VAR = 'HUTCH_PYTHON_AUTO_MONITOR'

# Acceptable values to make auto_monitor True
AUTO_TRUE = {'true', 't', 'yes', 'y', '1'}


def setup_ophyd():
    """
    Call EpicsSignalBase.set_defaults with pcds defaults.

    First, checks the following environment variables to set:
      - HUTCH_PYTHON_CONNECTION_TIMEOUT -> connection_timeout
      - HUTCH_PYTHON_READ_TIMEOUT -> timeout
      - HUTCH_PYTHON_WRITE_TIMEOUT -> write_timeout
      - HUTCH_PYTHON_AUTO_MONITOR -> auto_monitor

    If missing, default to the following behavior:

    Sets the following to the current ophyd defaults:
      - connection_timeout
      - timeout (read timeout)
      - auto_monitor

    Overriding defaults with themselves seems redundant, but I want to
    be insulated from changes to the upstream consensus.

    Sets a new default to the following:
      - write timeout (we don't want to wait forever)
    """
    EpicsSignalBase.set_defaults(
        connection_timeout=float(os.environ.get(CONN_VAR, 1.0)),
        timeout=float(os.environ.get(READ_VAR, 2.0)),
        write_timeout=float(os.environ.get(WRITE_VAR, 5.0)),
        auto_monitor=os.environ.get(AUTO_VAR, 'false').lower() in AUTO_TRUE,
        )
