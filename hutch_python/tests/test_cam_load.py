import logging

import pytest

from pcdsdevices.areadetector.detectors import PCDSDetector
from pcdsdevices.sim.pv import using_fake_epics_pv

from hutch_python.cam_load import (read_camviewer_cfg, interpret_lines,
                                   build_cam, UnsupportedConfig,
                                   MalformedConfig)

from .conftest import TST_CAM_CFG

logger = logging.getLogger(__name__)
CFG = TST_CAM_CFG.format('')


@using_fake_epics_pv
def test_build_cam():
    logger.debug('test_build_cam')
    # Basic functionality test
    obj = build_cam('GE:16', 'PREFIX:IMAGE2', None, 'my_cam')
    assert isinstance(obj, PCDSDetector)


@using_fake_epics_pv
def test_build_cam_errors():
    logger.debug('test_build_cam_errors')
    # Cover bad configs
    with pytest.raises(UnsupportedConfig):
        build_cam('asfd', '', '', '')

    with pytest.raises(MalformedConfig):
        build_cam('GE', '', '', '')


@using_fake_epics_pv
def test_read_camviewer_cfg():
    logger.debug('test_read_camviewer_cfg')
    # Basic functionality test
    objs = read_camviewer_cfg(CFG)
    assert isinstance(objs['my_cam'], PCDSDetector)
    assert len(objs) == 1


@using_fake_epics_pv
def test_include():
    logger.debug('test_include')
    objs = interpret_lines(['include ' + CFG,
                            'include'])
    assert isinstance(objs['my_cam'], PCDSDetector)
    assert len(objs) == 1
