import logging

from . import utils

logger = logging.getLogger(__name__)


def get_user_objs(load, *, ask_on_failure=True):
    """
    Load the user's modules.

    All objects from these modules will be imported e.g.
    ``from module import *`` and the objects will be returned.

    Parameters
    ----------
    load : str, list of str
        The module(s) to import.

    ask_on_failure : bool, optional
        If a module fails to load, indicate what happened and ask the user if
        loading should continue.

    Returns
    -------
    objs : dict
        Mapping from object name to object
    """
    if isinstance(load, str):
        load = [load]

    objs = {}
    for module in load:
        with utils.safe_load(module):
            try:
                module_objs = utils.extract_objs(module)
                objs.update(module_objs)
            except Exception as ex:
                if not ask_on_failure:
                    raise

                utils.maybe_exit(
                    logger,
                    message=(
                        f'Devices and functions from module {module} will NOT '
                        f'be available because it failed to load with:\n\t'
                        f'{ex.__class__.__name__}: {ex}'
                    ),
                    exception_message=f'Failed to load {module}',
                )

    return objs
