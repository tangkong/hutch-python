import logging
from importlib import import_module
from types import SimpleNamespace

from .utils import safe_load

logger = logging.getLogger(__name__)


def get_exp_objs(exp_module):
    """
    Load the correct experiment module.

    This will import User from ``experiments.{exp_module}``
    and create ``User()``, storing it as ``x``.

    Parameters
    ----------
    exp_module: ``str``
        The name of the experiment from the elog, without the hutch. This will
        be the name of the module loaded from the experiments folder.

    Returns
    -------
    user: ``object`` or ``SimpleNamespace``
        Either the user's class instantiated or a blank namespace for other
        experiment-specific objects to be attached to.
    """
    logger.debug('get_exp_objs(%s)', exp_module)
    module_name = 'experiments.' + exp_module
    with safe_load(exp_module):
        try:
            module = import_module(module_name)
            return module.User()
        except ImportError as exc:
            if module_name in exc.msg:
                logger.info('Skip missing experiment file %s.py', exp_module)
            else:
                raise
    return SimpleNamespace()
