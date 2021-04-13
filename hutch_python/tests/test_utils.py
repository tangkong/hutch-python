import logging

import IPython.lib.pretty as pretty
import pytest

from hutch_python import utils

logger = logging.getLogger(__name__)
_TEST = 4


def test_safe_load():
    logger.debug('test_safe_load')

    with utils.safe_load('zerodiv'):
        1/0

    with utils.safe_load('apples', cls='fruit'):
        apples = 4

    assert apples == 4


def test_get_current_experiment(fake_curexp_script):
    logger.debug('test_get_current_experiment')
    assert utils.get_current_experiment('tst') == 'tstlr1215'


def test_iterable_namespace():
    logger.debug('test_iterable_namespace')

    ns = utils.IterableNamespace(a=1, b=2, c=3)

    assert list(ns) == [1, 2, 3]
    assert len(ns) == 3


def test_helpful_namespace_pretty_print():
    class Obj:
        """Docstring"""

    ns = utils.HelpfulNamespace(obj_a=Obj(), obj_b=Obj())
    pretty_ns = pretty.pretty(ns)
    print("Pretty repr is", pretty_ns)
    assert "obj_a" in pretty_ns
    assert "obj_b" in pretty_ns
    assert "Docstring" in pretty_ns


def test_helpful_namespace_html_print():
    class Obj:
        """Docstring"""

    ns = utils.HelpfulNamespace(obj_a=Obj(), obj_b=Obj())
    html_ns = ns._repr_html_()
    assert "<td>obj_a</td>" in html_ns
    assert "<td>obj_b</td>" in html_ns
    assert "<td>Docstring</td>" in html_ns


def test_count_leaves():
    logger.debug('test_count_leaves')

    ns0 = utils.IterableNamespace(a=utils.IterableNamespace())
    ns1 = utils.IterableNamespace(a=1, b=utils.IterableNamespace())
    ns2 = utils.IterableNamespace(a=utils.IterableNamespace(a=1),
                                  b=utils.IterableNamespace(b=2))
    ns3 = utils.IterableNamespace(a=1,
                                  b=utils.IterableNamespace(a=1, b=2))

    assert utils.count_ns_leaves(ns0) == 0
    assert utils.count_ns_leaves(ns1) == 1
    assert utils.count_ns_leaves(ns2) == 2
    assert utils.count_ns_leaves(ns3) == 3


def test_extract_objs():
    logger.debug('test_extract_objs')
    # Has no __all__ keyword
    objs = utils.extract_objs('sample_module_1')
    assert objs['hey'] == '4horses'
    assert objs['milk'] == 'cows'
    assert objs['some_int'] == 5
    # Has an __all__ keyword
    objs = utils.extract_objs('sample_module_2.py')
    assert objs == dict(just_this=5.0)
    # Takes a list
    objs = utils.extract_objs(['sample_module_1', 'sample_module_2'])
    assert len(objs) == 5
    # Called with no scope, no skip hidden
    objs = utils.extract_objs(skip_hidden=False)
    assert objs['_TEST'] == 4


def test_find_class():
    logger.debug('test_find_class')
    # Find some standard type that needs an import
    found_Request = utils.find_class('urllib.request.Request')
    from urllib.request import Request
    assert found_Request is Request
    # Find some built-in type
    found_float = utils.find_class('float')
    assert found_float is float
    # Raises error if nothing is found
    with pytest.raises(ImportError):
        utils.find_class('aseoiajsdf')


def test_strip_prefix():
    logger.debug('test_strip_prefix')
    assert utils.strip_prefix('cats_dogs', 'cats') == 'dogs'
    assert utils.strip_prefix('cats', 'dogs') == 'cats'


def test_hutch_banner():
    logger.debug('test_hutch_banner')
    utils.hutch_banner()
    utils.hutch_banner('mfx')
