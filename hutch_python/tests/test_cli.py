import os
import shutil
import logging
from pathlib import Path

import pytest

from hutch_python.cli import main
from hutch_python.load_conf import load
import hutch_python.cli

from conftest import cli_args, restore_logging

logger = logging.getLogger(__name__)

CFG_PATH = Path(os.path.dirname(__file__)) / 'conf.yaml'
CFG = str(CFG_PATH)


@pytest.fixture(scope='function')
def no_ipython_launch(monkeypatch):
    def no_op(*args, **kwargs):
        pass
    monkeypatch.setattr(hutch_python.cli, 'start_ipython', no_op)


def test_main_normal(no_ipython_launch):
    logger.debug('test_main_normal')

    with cli_args(['hutch_python', '--cfg', CFG]):
        with restore_logging():
            main()


def test_main_no_args(no_ipython_launch):
    logger.debug('test_main_no_args')

    with cli_args(['hutch_python']):
        with restore_logging():
            main()


def test_debug_arg(no_ipython_launch):
    logger.debug('test_debug_arg')

    with cli_args(['hutch_python', '--cfg', CFG, '--debug']):
        with restore_logging():
            main()


def test_sim_arg(no_ipython_launch):
    logger.debug('test_sim_arg')

    with cli_args(['hutch_python', '--cfg', CFG, '--sim']):
        with restore_logging():
            main()


def create_arg_test(env=None):
    hutch = 'temp_create'
    test_dir = CFG_PATH.parent.parent.parent / hutch
    if test_dir.exists():
        shutil.rmtree(test_dir)

    with cli_args(['hutch_python', '--create', hutch]):
        with restore_logging():
            main()

    assert test_dir.exists()

    # Make sure conf.yml is valid
    load(str(test_dir / 'conf.yml'))

    # Make sure we picked the correct env
    if env is not None:
        with (test_dir / 'temp_createenv').open() as f:
            lines = f.readlines()
        has_env = False
        for line in lines:
            if 'CONDA_ENVNAME' in line:
                has_env = True
                assert env == line.split('"')[-2]
                break
        assert has_env

    shutil.rmtree(test_dir)


def test_create_arg_dev():
    logger.debug('test_create_arg_dev')
    create_arg_test()


def test_create_arg_prod(monkeypatch):
    logger.debug('test_create_arg_prod')
    monkeypatch.setattr(hutch_python.cli, 'CONDA_BASE', CFG_PATH.parent)
    create_arg_test('pcds-2.0.1')


def test_run_script():
    logger.debug('test_run_script')

    # Will throw a name error unless we run the script inside the full env
    with cli_args(['hutch_python', '--cfg', CFG, '--debug',
                   str(Path(__file__).parent / 'script.py')]):
        with restore_logging():
            main()
