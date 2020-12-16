import logging

import happi

from hutch_python.qs_load import get_qs_objs

logger = logging.getLogger(__name__)


def clear_happi_cache():
    happi.loader.cache = {}


def test_qs_load(fake_qsbackend):
    logger.debug('test_qs_load')
    clear_happi_cache()
    objs = get_qs_objs('tstlr1215')
    assert objs['inj_x'].run == '15'
    assert objs['inj_x'].proposal == 'LR12'
    assert objs['inj_x'].kerberos == 'True'
    # Check that we can handle an empty Questionnaire
    fake_qsbackend.empty = True
    assert get_qs_objs('tstlr1215') == dict()
    fake_qsbackend.empty = False


def test_ws_auth_conf(temporary_config, fake_qsbackend):
    logger.debug('test_ws_auth_conf')
    clear_happi_cache()
    objs = get_qs_objs('tstlr1215')
    assert objs['inj_x'].kerberos == 'False'
    assert objs['inj_x'].user == 'user'
    assert objs['inj_x'].pw == 'pw'
