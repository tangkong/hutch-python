import logging

from pcdsdevices.interface import BaseInterface, set_engineering_mode

from hutch_python.user_load import get_user_objs, update_whitelist
from hutch_python.utils import HelpfulNamespace

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


def test_load_tab_whitelist():

    class MyTest(BaseInterface):
        THIS_SHOULD_NOT_BE_THERE = None
        tab_whitelist = ['foo']
        foo = 'f'
        bar = 'b'

    set_engineering_mode(False)
    a = MyTest()
    ns = HelpfulNamespace(a=a)

    # __dir__() as a proxy for tab completion.  We test tab
    # completion setup elsewhere.
    assert 'foo' in a.__dir__()
    assert 'bar' not in a.__dir__()

    update_whitelist(ns, 'a', ['bar'])
    assert 'bar' in a.__dir__()
