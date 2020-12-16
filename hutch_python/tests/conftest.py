import logging
import os
import sys
from collections import namedtuple
from contextlib import contextmanager
from copy import copy
from logging.handlers import QueueHandler
from pathlib import Path
from queue import Queue

import pytest
from elog import HutchELog
from epics import PV
from ophyd.areadetector.plugins import PluginBase
from ophyd.device import Component as Cpt
from ophyd.signal import Signal
from pcdsdevices.areadetector.detectors import PCDSAreaDetector

import hutch_python.qs_load
import hutch_python.utils

# We need to have the tests directory importable to match what we'd have in a
# real hutch-python install
sys.path.insert(0, os.path.dirname(__file__))

TST_CAM_CFG = str(Path(__file__).parent / '{}camviewer.cfg')

for component in PCDSAreaDetector.component_names:
    cpt_class = getattr(PCDSAreaDetector, component).cls
    if issubclass(cpt_class, PluginBase):
        cpt_class.plugin_type = Cpt(Signal, value=cpt_class._plugin_type)

# Stupid patch that somehow makes the test cleanup bug go away
PV.count = property(lambda self: 1)


@contextmanager
def cli_args(args):
    """
    Context manager for running a block of code with a specific set of
    command-line arguments.
    """
    prev_args = sys.argv
    sys.argv = args
    yield
    sys.argv = prev_args


@contextmanager
def restore_logging():
    """
    Context manager for reverting our logging config after testing a function
    that configures the logging.
    """
    prev_handlers = copy(logging.root.handlers)
    yield
    logging.root.handlers = prev_handlers


@pytest.fixture(scope='function')
def log_queue():
    with restore_logging():
        my_queue = Queue()
        handler = QueueHandler(my_queue)
        root_logger = logging.getLogger('')
        root_logger.addHandler(handler)
        yield my_queue


Experiment = namedtuple('Experiment', ('run', 'proposal',
                                       'user', 'pw', 'kerberos'))


class QSBackend:
    empty = False

    def __init__(self, expname, use_kerberos=True, user=None, pw=None):
        self.expname = expname
        self.user = user
        self.pw = pw
        self.kerberos = use_kerberos

        if 'bad' in expname:
            raise RuntimeError('bad expname')

    def find(self, to_match):
        device = {
            '_id': 'TST:USR:MMN:01',
            'beamline': 'TST',
            'device_class': 'hutch_python.tests.conftest.Experiment',
            'location': 'Hutch-main experimental',
            'args': ['{{run}}', '{{proposal}}',
                     '{{user}}', '{{pw}}', '{{kerberos}}'],
            'kwargs': {},
            'name': 'inj_x',
            'prefix': 'TST:USR:MMN:01',
            'purpose': 'Injector X',
            'type': 'pcdsdevices.happi.containers.LCLSItem',
            'run': self.expname[-2:],
            'user': self.user,
            'pw': self.pw,
            'kerberos': self.kerberos,
            'proposal': self.expname[3:-2].upper()}
        if self.empty:
            return
        else:
            yield device
            return

    # Dummy methods to make this "look like a database"
    def all_devices(self, *args, **kwargs):
        pass

    def all_items(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        pass


@pytest.fixture(scope='function')
def fake_qsbackend(monkeypatch):
    monkeypatch.setattr(hutch_python.qs_load, "QSBackend", QSBackend)
    QSBackend.empty = False
    return QSBackend


cfg = """\
[DEFAULT]
user=user
pw=pw
[GITHUB]
user=github_user
pw=github_pw
proxy=http://proxyhost:11111
"""


@pytest.fixture(scope='function')
def temporary_config():
    # Write to our configuration
    with open('web.cfg', '+w') as f:
        f.write(cfg)
    # Allow the test to run
    yield
    # Remove the file
    os.remove('web.cfg')


@pytest.fixture(scope='function')
def fake_curexp_script():
    old_script = hutch_python.utils.CUR_EXP_SCRIPT
    hutch_python.utils.CUR_EXP_SCRIPT = 'echo {}lr1215'
    yield
    hutch_python.utils.CUR_EXP_SCRIPT = old_script


class ELog(HutchELog):
    """Pseudo ELog"""
    def __init__(self, instrument, station=None, user=None, pw=None):
        self.instrument = instrument
        self.station = station
        self.user = user
        self.pw = pw
