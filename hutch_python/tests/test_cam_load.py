import logging

import pytest
from pcdsdevices.areadetector.detectors import PCDSAreaDetector

from hutch_python.cam_load import (MalformedConfig, UnsupportedConfig,
                                   build_and_log, build_cam, interpret_lines,
                                   read_camviewer_cfg)

from .conftest import TST_CAM_CFG

logger = logging.getLogger(__name__)
CFG = TST_CAM_CFG.format('')


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
