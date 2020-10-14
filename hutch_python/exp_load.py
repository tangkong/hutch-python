import logging
from importlib import import_module
from types import SimpleNamespace

from . import utils

logger = logging.getLogger(__name__)


def get_exp_objs(exp_module, *, ask_on_failure=True):
    """
    Load the correct experiment module.

    This will import User from ``experiments.{exp_module}``
    and create ``User()``, storing it as ``x``.

    Parameters
    ----------
    exp_module: ``str``
        The name of the experiment from the elog, without the hutch. This will
        be the name of the module loaded from the experiments folder.

    ask_on_failure : bool, optional
        If a module fails to load, indicate what happened and ask the user if
        loading should continue.

    Returns
    -------
    user: ``object`` or ``SimpleNamespace``
        Either the user's class instantiated or a blank namespace for other
        experiment-specific objects to be attached to.
    """
    logger.debug('get_exp_objs(%s)', exp_module)
    module_name = 'experiments.' + exp_module
    with utils.safe_load(exp_module):
        try:
            module = import_module(module_name)
            return module.User()
        except Exception as ex:
            import_err = isinstance(ex, ImportError) and module_name in ex.msg
            if import_err or not ask_on_failure:
                logger.info('Skip missing experiment file %s.py', exp_module)
                return SimpleNamespace()

            utils.maybe_exit(
                logger,
                message=(
                    f'Devices and functions from module {module_name} will NOT'
                    f' be available because it failed to load with:\n\t'
                    f'{ex.__class__.__name__}: {ex}'
                ),
                exception_message=f'Failed to load {module_name}',
            )

    return SimpleNamespace()
