import logging
from pathlib import Path
from typing import Union

import yaml

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


def configure_objects(
    obj_config: Union[str, Path],
    objs: utils.HelpfulNamespace
) -> utils.HelpfulNamespace:
    """
    Configure objects based on user provided settings.

    Parameters
    -----------
    obj_config : Pathlike
        Path to configuration yml file

    objs : HelpfulNamespsace
        All objects to be loaded into hutch-python

    Returns
    -------
    objs : HelpfulNamespace
        Modified objects
    """
    with utils.safe_load('configure user objects'):
        # load yaml
        with open(obj_config, 'r') as f:
            cfg = yaml.safe_load(f)

        # apply changes to each device
        for dev in cfg:
            # apply each valid configuration action
            if 'tab_whitelist' in cfg[dev]:
                update_whitelist(objs, dev,
                                 cfg['dev']['tab_whitelist'])

        return objs


def update_whitelist(obj_ns: utils.HelpfulNamespace,
                     device: str,
                     attrs: list[str]) -> None:
    """
    Update ``device``'s tab completion whitelist to include ``items``
    Device is assumed to be in ``obj_ns``

    Parameters
    ----------
    obj_ns : HelpfulNamespace
        Namespace of all objects

    device : str
        Name of device to edit

    attrs : list[str]
        List of attributes to add to whitelist
    """
    try:
        dev = obj_ns[device]
    except KeyError:
        logger.warn(f'{device} not loaded, cannot configure')

    for att in attrs:
        dev._tab.add(att)
