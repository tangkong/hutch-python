"""
Module to contain ophyd-specific settings that must be applied prior to
creating any ophyd objects.
"""
from ophyd.signal import EpicsSignalBase


def setup_ophyd():
    """
    Call EpicsSignalBase.set_defaults with pcds defaults.

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
        connection_timeout=1.0,
        timeout=2.0,
        write_timeout=5.0,
        auto_monitor=False,
        )

