import logging

import pytest
from ophyd import Component as Cpt
from ophyd import Device, Kind, Signal
from pcdsdevices.interface import BaseInterface, set_engineering_mode

from hutch_python.obj_config import (replace_tablist, update_blacklist,
                                     update_kind, update_objs,
                                     update_whitelist)
from hutch_python.utils import HelpfulNamespace

logger = logging.getLogger(__name__)


class MyTest(BaseInterface, Device):
    THIS_SHOULD_NOT_BE_THERE = None
    tab_whitelist = ['foo']
    foo = 'f'
    bar = 'b'
    sig = Cpt(Signal, kind='normal')


@pytest.fixture
def objs(request):
    set_engineering_mode(False)
    a = MyTest(name='a')
    b = MyTest(name='b')
    if request.param == 'flat':
        ns = HelpfulNamespace(a=a, b=b)
    elif request.param == 'nested':
        ns = HelpfulNamespace(a=a, ns=HelpfulNamespace(b=b))
    return (ns, a, b)


@pytest.mark.parametrize(
    'objs', ['flat', 'nested'], indirect=True
)
def test_tab_whitelist(objs):
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
def test_tab_blacklist(objs):
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


@pytest.mark.parametrize(
    'objs', ['flat', 'nested'], indirect=True
)
def test_replace_tablist(objs):
    ns, dev_a, dev_b = objs
    cfg = {'a': {'replace_tablist': ['bar']},
           'b': {'replace_tablist': ['foo', 'dne']}}

    update_objs(ns, 'a', cfg['a']['replace_tablist'],
                replace_tablist)
    assert 'bar' in dir(dev_a)
    assert 'foo' not in dir(dev_a)
    assert 'foo' in dir(dev_b)

    assert 'dne' not in dir(dev_b)
    update_objs(ns, 'b', cfg['b']['replace_tablist'],
                replace_tablist)
    assert 'foo' in dir(dev_b)
    assert 'bar' not in dir(dev_b)
    assert 'dne' not in dir(dev_b)


@pytest.mark.parametrize(
    'objs', ['flat', 'nested'], indirect=True
)
def test_update_kind(objs):
    ns, dev_a, dev_b = objs
    cfg = {'a': {'kind': {'sig': 'hinted'}},
           'b': {'kind': {'dne': 'dnekind', 'sig': 'config', }}}

    assert dev_a.sig.kind == Kind.normal
    assert dev_b.sig.kind == Kind.normal

    update_objs(ns, 'a', cfg['a']['kind'],
                update_kind)
    assert dev_a.sig.kind == Kind.hinted

    update_objs(ns, 'b', cfg['b']['kind'],
                update_kind)
    assert dev_b.sig.kind == Kind.config
