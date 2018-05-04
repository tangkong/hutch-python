import logging
from pathlib import Path

import pytest

from ophyd.device import Component as Cpt
from ophyd.signal import Signal

from pcdsdevices.areadetector.detectors import PCDSDetector
from pcdsdevices.sim.pv import using_fake_epics_pv

from hutch_python.cam_load import (read_cfg, interpret_lines, build_cam,
                                   UnsupportedConfig, MalformedConfig)

logger = logging.getLogger(__name__)

CFG = str(Path(__file__).parent / 'camviewer.cfg')

for plugin in ('image', 'stats'):
    plugin_class = getattr(PCDSDetector, plugin).cls
    plugin_class.plugin_type = Cpt(Signal, value=plugin_class._plugin_type)


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
def test_read_cfg():
    logger.debug('test_read_cfg')
    # Basic functionality test
    objs = read_cfg(CFG)
    assert isinstance(objs['my_cam'], PCDSDetector)
    assert len(objs) == 1


@using_fake_epics_pv
def test_include():
    logger.debug('test_include')
    objs = interpret_lines(['include ' + CFG,
                            'include'])
    assert isinstance(objs['my_cam'], PCDSDetector)
    assert len(objs) == 1
