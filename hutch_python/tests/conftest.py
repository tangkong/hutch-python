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
import zmq
from epics import PV
from ophyd.areadetector.base import EpicsSignalWithRBV
from ophyd.areadetector.plugins import PluginBase
from ophyd.device import Component as Cpt
from ophyd.ophydobj import OphydObject
from ophyd.signal import Signal
from ophyd.sim import FakeEpicsSignal, fake_device_cache, make_fake_device
from pcdsdevices.areadetector.detectors import PCDSAreaDetector

import hutch_python.cam_load as cam_load
import hutch_python.qs_load
import hutch_python.utils

try:
    from elog import HutchELog
except ImportError:
    HutchELog = None
try:
    import lightpath
    from lightpath.config import beamlines, sources

    # patch lightpath config to have proper lines/sources
    beamlines['TST'] = ['X0']
    sources.append('X0')
except ImportError:
    lightpath = None
    beamlines = None
    sources = None
try:
    from psdaq.control.BlueskyScan import BlueskyScan
except ImportError:
    BlueskyScan = None


# Some re-usable skip decorators
skip_if_win32_generic = pytest.mark.skipif(
    sys.platform == 'win32',
    reason='Does not run on Windows',
)
skip_if_win32_pcdsdaq = pytest.mark.skipif(
    sys.platform == 'win32',
    reason='Fails on Windows (pcdsdaq)',
)
requires_lightpath = pytest.mark.skipif(
    lightpath is None,
    reason='lightpath module not installed',
)
requires_elog = pytest.mark.skipif(
    HutchELog is None,
    reason='elog module not installed',
)
requires_psdaq = pytest.mark.skipif(
    BlueskyScan is None,
    reason='psdaq.control not installed',
)

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
    def clear_cache(self, *args, **kwargs):
        pass

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


if HutchELog is None:
    ELog = None
else:
    class ELog(HutchELog):
        """Pseudo ELog"""
        def __init__(self, instrument, station=None, user=None, pw=None):
            self.instrument = instrument
            self.station = station
            self.user = user
            self.pw = pw


class DummyZMQContext:
    def __init__(self, *args, **kwargs):
        pass

    def socket(self, *args, **kwargs):
        return DummyZMQSocket()


class DummyZMQSocket:
    def __init__(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass

    def setsockopt(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def bind(self, *args, **kwargs):
        pass

    def send_json(self, *args, **kwargs):
        pass

    def recv_json(self, *args, **kwargs):
        return {}

    def send(self, *args, **kwargs):
        pass

    def recv(self, *args, **kwargs):
        # Trick the fake daq into stopping itself
        return b"shutdown"


@pytest.fixture(scope='function')
def dummy_zmq_lcls2(monkeypatch):
    # monkeypatch such that the lcls2 daq doesn't actually connect to things
    monkeypatch.setattr(zmq, 'Context', DummyZMQContext)


this_test_ophydobj = []


@pytest.fixture(scope='session', autouse=True)
def register_ophydobj():
    """
    Save references to all the ophydobj we create.
    """
    OphydObject.add_instantiation_callback(this_test_ophydobj.append)


@pytest.fixture(scope='function', autouse=True)
def cleanup_ophydobj():
    """
    Disable ophydobj that were created by the test.

    We need to do this or they can persist between tests, clogging the logs
    as the PVs update and causing race conditions.
    """
    yield
    for obj in this_test_ophydobj:
        # Should probably destroy here but it segfaults
        # Need to remove all subs, disable the monitor, remove callbacks
        # Might fail on non-pyepics idk
        obj.unsubscribe_all()
        for pv_attr in ('_read_pv', '_write_pv'):
            try:
                pv = getattr(obj, pv_attr)
            except AttributeError:
                pass
            else:
                pv.auto_monitor = False
                pv.clear_callbacks()
    this_test_ophydobj.clear()


@pytest.fixture(autouse=True)
def patch_areadet():
    fake_device_cache[EpicsSignalWithRBV] = FakeEpicsSignal
    FakeDet = make_fake_device(PCDSAreaDetector)
    cam_load.PCDSAreaDetector = FakeDet
