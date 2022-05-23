import logging

from hutch_python.user_load import get_user_objs

logger = logging.getLogger(__name__)


def test_user_load():
    logger.debug('test_user_load')
    info = ['sample_module_1', 'sample_module_2.py']
    objs = get_user_objs(info, ask_on_failure=False)
    assert objs['hey'] == '4horses'
    assert objs['milk'] == 'cows'
    assert objs['some_int'] == 5
    assert objs['just_this'] == 5.0
    assert 'not_this' not in objs
