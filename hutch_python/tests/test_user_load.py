import logging

import pytest
from pcdsdevices.interface import BaseInterface, set_engineering_mode

from hutch_python.user_load import (get_user_objs, update_blacklist,
                                    update_objs, update_whitelist)
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


class MyTest(BaseInterface):
    THIS_SHOULD_NOT_BE_THERE = None
    tab_whitelist = ['foo']
    foo = 'f'
    bar = 'b'


@pytest.fixture
def objs(request):
    set_engineering_mode(False)
    a = MyTest()
    b = MyTest()
    if request.param == 'flat':
        ns = HelpfulNamespace(a=a, b=b)
    elif request.param == 'nested':
        ns = HelpfulNamespace(a=a, ns=HelpfulNamespace(b=b))
    return (ns, a, b)


@pytest.mark.parametrize(
    'objs', ['flat', 'nested'], indirect=True
)
def test_indirect(objs):
    ns, dev_a, dev_b = objs
    cfg = {'a': {'tab_whitelist': ['bar']},
           'b': {'tab_whitelist': ['bar', 'dne']}}

    assert 'bar' not in dir(dev_a)
    assert 'bar' not in dir(dev_b)
    update_objs(ns, 'a', cfg['a']['tab_whitelist'],
                update_whitelist)
    assert 'bar' in dir(dev_a)
    assert 'bar' not in dir(dev_b)

    update_objs(ns, 'b', cfg['b']['tab_whitelist'],
                update_whitelist)
    assert 'bar' in dir(dev_b)
    assert 'dne' not in dir(dev_b)


@pytest.mark.parametrize(
    'objs', ['flat', 'nested'], indirect=True
)
def test_load_tab_blacklist(objs):
    ns, dev_a, dev_b = objs
    cfg = {'a': {'tab_blacklist': ['bar']},
           'b': {'tab_blacklist': ['foo', 'dne']}}

    update_objs(ns, 'a', cfg['a']['tab_blacklist'],
                update_blacklist)
    assert 'bar' not in dir(dev_a)
    assert 'foo' in dir(dev_b)

    assert 'dne' not in dir(dev_b)
    update_objs(ns, 'b', cfg['b']['tab_blacklist'],
                update_blacklist)
    assert 'foo' not in dir(dev_b)
    assert 'dne' not in dir(dev_b)
