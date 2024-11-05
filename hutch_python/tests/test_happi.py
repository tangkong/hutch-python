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


# run test_happi_objs() with exclude_devices
@conftest.requires_lightpath
def test_happi_objs_with_exclude_devices():
    # This test checks whether devices from exclude_devices have been removed from the
    # output of get_happi_objs(). For comparison, get_happi_objs() is first called without
    # exclude_devices and then called again with exclude_devices.
    exclude_devices = ['tst_device_5', 'tst_device_1']

    logger.debug("test_happi_objs")
    db = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                      'happi_db.json')
    # Only select active objects
    lc = get_lightpath(db, 'tst')

    # Load all devices
    objs = get_happi_objs(db, lc, 'tst', DeviceLoadLevel.STANDARD)
    assert len(objs) == 4

    # Do not load excluded devices
    objs_exclude_devices = get_happi_objs(db, lc, 'tst', DeviceLoadLevel.STANDARD, exclude_devices)
    assert len(objs_exclude_devices) == 2

    # Check that none of the loaded devices are in the exclude_devices list
    for obj in objs_exclude_devices:
        assert obj not in exclude_devices
