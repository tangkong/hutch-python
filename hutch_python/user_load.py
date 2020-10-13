import logging
import sys

from .utils import extract_objs, safe_load

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
        with safe_load(module):
            try:
                module_objs = extract_objs(module)
                objs.update(module_objs)
            except Exception as ex:
                if not ask_on_failure:
                    raise

                # Dump out the full exception first, before a friendlier
                # message and querying the user.
                logger.exception('Failed to load %s', module)
                logger.error(
                    'Devices and functions from module %r will NOT be '
                    'available because it failed to load with:\n\t %s: %s.',
                    module, ex.__class__.__name__, ex
                )

                response = input('Continue loading hutch-python? [Yn] ')
                if response.lower() not in {'y', ''}:
                    sys.exit(1)

    return objs
