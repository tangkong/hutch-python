import logging
import os.path
import tempfile

import pytest
import simplejson

from hutch_python.happi import DeviceLoadLevel, get_happi_objs, get_lightpath

from . import conftest

logger = logging.getLogger(__name__)


@conftest.requires_lightpath
def test_happi_objs():
    logger.debug("test_happi_objs")
    db = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      'happi_db.json')
    # patch lightpath configs to include test db beamline
    conftest.beamlines['TST'] = ['X0']
    conftest.sources.append('X0')
    # Only select active objects
    lc = get_lightpath(db, 'tst')
    objs = get_happi_objs(db, lc, 'tst')
    assert len(objs) == 4
    assert all([obj.md.active for obj in objs.values()])
    # Make sure we can handle an empty JSON file
    with tempfile.NamedTemporaryFile('w+') as tmp:
        simplejson.dump(dict(), tmp)
        tmp.seek(0)
        with pytest.raises(ValueError):
            # light controller will raise if no devices are found
            lc = get_lightpath(tmp.name, 'tst')


@pytest.mark.parametrize('load_level, num_devices', [
    (DeviceLoadLevel.UPSTREAM, 3),
    (DeviceLoadLevel.STANDARD, 4),
    (DeviceLoadLevel.ALL, 5)
])
@conftest.requires_lightpath
def test_load_level(load_level: DeviceLoadLevel, num_devices: int):
    logger.debug("test_load_level")
    db = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      'happi_db.json')
    # patch lightpath configs to include test db beamline
    conftest.beamlines['TST'] = ['X0']
    conftest.sources.append('X0')
    # Only select active objects
    lc = get_lightpath(db, 'tst')
    objs = get_happi_objs(db, lc, 'tst', load_level=load_level)
    assert len(objs) == num_devices


@conftest.requires_lightpath
def test_get_lightpath():
    logger.debug("test_get_lightpath")
    db = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      'happi_db.json')
    lc = get_lightpath(db, 'tst')
    obj = lc.active_path('tst'.upper())
    # Check that we created a valid BeamPath with no inactive objects
    assert obj.name == 'TST'
    assert len(obj.devices) == 3


# run test_happi_objs() without the excluded devices
@conftest.requires_lightpath
def test_happi_objs_without_exclude_devices():
    logger.debug("test_happi_objs")
    db = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      'happi_db.json')
    # patch lightpath configs to include test db beamline
    conftest.beamlines['TST'] = ['X0']
    conftest.sources.append('X0')
    # Only select active objects
    lc = get_lightpath(db, 'tst')
    # in DeviceLoadLevel.STANDARD you search happi and look for devices with same beamline name
    objs = get_happi_objs(db, lc, 'tst', DeviceLoadLevel.STANDARD)
    assert len(objs) == 4


# run test_happi_objs() with exclude_devices
@conftest.requires_lightpath
def test_happi_objs_with_exclude_devices():
    logger.debug("test_happi_objs")
    db = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      'happi_db.json')
    # patch lightpath configs to include test db beamline
    conftest.beamlines['TST'] = ['X0']
    conftest.sources.append('X0')
    # Only select active objects
    lc = get_lightpath(db, 'tst')
    # get devices not in excluded_devices list
    exclude_devices = ['tst_device_5', 'tst_device_1']
    objs = get_happi_objs(
        db, lc, 'tst', DeviceLoadLevel.STANDARD, exclude_devices)
    exclude_devices = ['tst_device_5', 'tst_device_1']
    assert len(objs) == 2
    for obj in objs:
        assert obj not in exclude_devices
