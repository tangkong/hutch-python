import logging
from types import SimpleNamespace

from hutch_python.exp_load import get_exp_objs

logger = logging.getLogger(__name__)


def test_experiment_objs():
    logger.debug('test_experiment_objs')

    user = get_exp_objs('sample_expname')
    assert not isinstance(user, SimpleNamespace)

    empty = get_exp_objs('q3qwer')
    assert isinstance(empty, SimpleNamespace)
