import json
import logging
import os
from unittest.mock import patch

import happi
import pytest
from conftest import cli_args

import hutch_python
import hutch_python.constants
import hutch_python.epics_arch
import hutch_python.qs_load

from ..epics_arch import (create_file, main, overwrite_hutch, overwrite_path,
                          print_dry_run, set_path, get_items)

logger = logging.getLogger(__name__)


def test_epics_arch_args():
    with cli_args(['epicsarch-qs', 'xpplv6818']):
        with patch('hutch_python.epics_arch.create_file') as mock:
            main()
        mock.assert_called_once()


def test_overwrite_hutch_args():
    with cli_args(['epicsarch-qs', '--hutch', 'xpp']):
        with patch('hutch_python.epics_arch.overwrite_hutch') as mock:
            main()
        mock.assert_called_once()


def test_overwrite_path_args():
    with cli_args(['epicsarch-qs', '--path', '/xpp/my/path/']):
        with patch('hutch_python.epics_arch.overwrite_path') as mock:
            main()
        mock.assert_called_once()


@patch('hutch_python.epics_arch.create_file')
@patch('hutch_python.epics_arch.overwrite_hutch')
def test_overwrite_hutch_with_exp_args(hutch_mock, create_mock):
    with cli_args(['epicsarch-qs', 'xpplv6818', '--hutch', 'xpp']):
        with patch('hutch_python.epics_arch.get_items', return_value=items):
            main()
        hutch_mock.assert_called_once()
        create_mock.assert_called_once()


@patch('hutch_python.epics_arch.create_file')
@patch('hutch_python.epics_arch.overwrite_path')
def test_overwrite_path_with_exp_args(hutch_mock, create_mock):
    with cli_args(['epicsarch-qs', 'xpplv6818', '--path', '/my/path/xpp/']):
        with patch('hutch_python.epics_arch.get_items', return_value=items):
            main()
        hutch_mock.assert_called_once()
        create_mock.assert_called_once()


@patch('hutch_python.epics_arch.get_questionnaire_data')
def test_dry_run_args(get_data_mock, items):
    with cli_args(['epicsarch-qs', 'xpplv6818', '--dry-run']):
        with patch('hutch_python.epics_arch.get_items', return_value=items):
            with patch('hutch_python.epics_arch.print_dry_run') as mock:
                main()
            mock.assert_called_once()
            get_data_mock.assert_called_once


def test_dry_run_args_exception():
    with pytest.raises(Exception):
        get_items('somebadname')


def test_overwrite_hutch():
    overwrite_hutch('xpp')
    assert hutch_python.constants.EPICS_ARCH_FILE_PATH == (
        '/cds/group/pcds/dist/pds/xpp/misc/'
        )


def test_overwrite_path():
    with patch('os.path.exists', return_value=True):
        overwrite_path('/my/dummy/path/')
        assert hutch_python.constants.EPICS_ARCH_FILE_PATH == '/my/dummy/path/'


def test_overwrite_bad_path():
    with pytest.raises(OSError):
        overwrite_path('/my/dummy/path/')


def test_set_path():
    set_path('xcslv6818')
    assert hutch_python.constants.EPICS_ARCH_FILE_PATH == (
        '/cds/group/pcds/dist/pds/xcs/misc/'
        )


def test_print_dry_run(items, capsys):
    with patch('hutch_python.epics_arch.get_items', return_value=items):
        expected_list = [
            '* tape_x', 'XPP:LBL:MMN:04', '* transducer_y',
            'XPP:LBL:MMN:05', '* xes_y', 'XPP:LBL:MMN:06', '* lbl',
            'XPP:USR:EVR:TRIG0', '* acromag', 'XPP:USR:ao1'
            ]
        expected_str = ''
        for m in expected_list:
            expected_str += m + '\n'

        print_dry_run('xpplv6818')
        readout = capsys.readouterr()
        assert expected_str in readout


def test_create_file(items):
    dir_path = os.path.dirname(os.path.realpath(__file__)) + '/'
    with patch('hutch_python.epics_arch.get_items', return_value=items):
        create_file('tstlr3216', path=dir_path)
        expected_file = ''.join((dir_path, 'epicsArch_tstlr3216.txt'))
        expected_list = [
            '* tape_x', 'XPP:LBL:MMN:04', '* transducer_y',
            'XPP:LBL:MMN:05', '* xes_y', 'XPP:LBL:MMN:06', '* lbl',
            'XPP:USR:EVR:TRIG0', '* acromag', 'XPP:USR:ao1']
        temp_list = [line.rstrip('\n') for line in open(expected_file)]
        # Check that the file was made
        assert os.path.exists(expected_file)
        assert temp_list == expected_list
        # Cleanup
        os.remove(expected_file)


def test_create_file_bad_path(items):
    with patch('hutch_python.epics_arch.get_items', return_value=items):
        with pytest.raises(OSError):
            create_file('tstlr3216', path='/some/bad/path/')


@pytest.fixture(scope='function')
def json_db(tmp_path_factory):
    dir_path = tmp_path_factory.mktemp("db_dir")
    json_path = dir_path / 'db.json'
    json_path.write_text(json.dumps(all_items))
    return str(json_path.absolute())


@pytest.fixture(scope='function')
def items(json_db):
    client = happi.client.Client(path=json_db)
    return client.all_items


all_items = json.loads("""{
            "tape_x": {
                "_id": "tape_x",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "tape_x",
                "prefix": "XPP:LBL:MMN:04",
                "type": "pcdsdevices.happi.containers.Motor",
                "location": "XPP goniometer",
                "purpose": "Tape X",
                "pvbase": "XPP:LBL:MMN:04",
                "stageidentity": "Newport"
                },
            "transducer_y": {
                "_id": "transducer_y",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "transducer_y",
                "prefix": "XPP:LBL:MMN:05",
                "type": "pcdsdevices.happi.containers.Motor",
                "location": "XPP goniometer",
                "purpose": "Transducer Y",
                "stageidentity": "Newport",
                "pvbase": "XPP:LBL:MMN:05"
                },
            "xes_y": {
                "_id": "xes_y",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "xes_y",
                "prefix": "XPP:LBL:MMN:06",
                "type": "pcdsdevices.happi.containers.Motor",
                "location": "XPP goniometer",
                "stageidentity": "Newport",
                "purpose": "Xes Epix Y",
                "pvbase": "XPP:LBL:MMN:06"
                },
            "lbl": {
                "_id": "lbl",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "lbl",
                "prefix": "XPP:USR:EVR:TRIG0",
                "type": "pcdsdevices.happi.containers.Trigger",
                "purpose": "LBL",
                "width": "1e-5",
                "polarity": "positiv",
                "delay": "0.0008",
                "pvbase": "XPP:USR:EVR:TRIG0",
                "eventcode": "42"
                },
            "acromag": {
                "_id": "acromag",
                "active": true,
                "args": ["{{prefix}}"],
                "beamline": "XPP",
                "kwargs": {"name": "{{name}}"},
                "lightpath": false,
                "name": "acromag",
                "prefix": "XPP:USR:ao1",
                "type": "pcdsdevices.happi.containers.Acromag",
                "device": "Acromag IP231 16-bit",
                "pvbase": "XPP:USR:ao1",
                "purpose": "Evo Shutter 1",
                "channel": "6"
                }
                }
                """)
