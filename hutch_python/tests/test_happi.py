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
