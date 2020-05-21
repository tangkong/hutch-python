import logging

from ophyd.areadetector.base import EpicsSignalWithRBV
from ophyd.sim import make_fake_device, fake_device_cache, FakeEpicsSignal
import pytest

from pcdsdevices.areadetector.detectors import PCDSAreaDetector

import hutch_python.cam_load as cam_load
from hutch_python.cam_load import (read_camviewer_cfg, interpret_lines,
                                   build_and_log, build_cam,
                                   UnsupportedConfig, MalformedConfig)

from .conftest import TST_CAM_CFG

logger = logging.getLogger(__name__)
CFG = TST_CAM_CFG.format('')

fake_device_cache[EpicsSignalWithRBV] = FakeEpicsSignal
FakeDet = make_fake_device(PCDSAreaDetector)
cam_load.PCDSAreaDetector = FakeDet


def test_build_cam():
    logger.debug('test_build_cam')
    # Basic functionality test
    obj = build_cam('GE:16', 'PREFIX:IMAGE2', None, 'my_cam')
    assert isinstance(obj, PCDSAreaDetector)


def test_build_cam_errors():
    logger.debug('test_build_cam_errors')
    # Cover bad configs
    with pytest.raises(UnsupportedConfig):
        build_cam('asfd', '', '', '')

    with pytest.raises(MalformedConfig):
        build_cam('GE', '', '', '')


def test_read_camviewer_cfg():
    logger.debug('test_read_camviewer_cfg')
    # Basic functionality test
    objs = read_camviewer_cfg(CFG)
    assert isinstance(objs['my_cam'], PCDSAreaDetector)
    assert len(objs) == 1


def test_include():
    logger.debug('test_include')
    info = interpret_lines(['include ' + CFG,
                            'include'])
    assert len(info) == 4


def test_bad_object():
    logger.debug('test_bad_object')
    # Shouldn't get a full raise out of build_and_log when obj is bad
    build_and_log(['GE', logger, None, 'bad'])
