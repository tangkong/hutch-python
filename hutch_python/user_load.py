import logging
from pathlib import Path
from typing import Callable, Tuple, Union

import yaml
from ophyd import Kind
from pcdsdevices.interface import BaseInterface

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


def update_objs(
    obj_ns: utils.HelpfulNamespace,
    entry: str,
    attrs: dict,
    fn: Callable[[BaseInterface, Union[dict, list[str]]], None]
) -> None:
    """
    Helper function for updating object namespaces
    obj_ns is a HelpfulNamespace, which may include other
    HelpfulNamespace's.  As a result this must be semi-recursive.

    Parameters
    ----------
    obj_ns : HelpfulNamespace
        Namespace of all objects

    entry : str
        Name of device to edit

    attrs : list[str]
        List of attributes to add to whitelist

    fn : Callable[[BaseInterface, dict], None]
        A function that applies a change to a singular device
    """
    dev = getattr(obj_ns, entry, None)
    if dev:  # look for explicit device
        fn(dev, attrs)

        return

    # look for devices with class
    for dev in obj_ns:
        if isinstance(dev, utils.HelpfulNamespace):
            update_objs(dev, entry, attrs, fn)
        # a poor-man's type check, in an effort to avoid importing
        # every device type again
        if entry in str(type(dev)):
            fn(dev, attrs)


def update_whitelist(dev: BaseInterface, attrs: list[str]) -> None:
    """
    Update the tab whitelist for ``dev`` with each field in ``attrs``

    Parameters
    ----------
    dev : BaseInterface
        A single object implementing the tab completion features in
        pcdsdevices.interface.BaseInterface

    attrs : list[str]
        list of attributes to add to ``dev`` tablist
    """
    for att in attrs:
        dev._tab.add(att)


def update_blacklist(dev: BaseInterface, attrs: list[str]) -> None:
    """
    Remove each field in ``attrs`` from tab whitelist for ``dev``

    Parameters
    ----------
    dev : BaseInterface
        A single object implementing the tab completion features in
        pcdsdevices.interface.BaseInterface

    attrs : list[str]
        list of attributes to remove from ``dev`` tablist
    """
    for att in attrs:
        try:
            dev._tab.remove(att)
        except KeyError:
            logger.debug(f'key: {att} not in tab completion list')


def replace_tablist(dev: BaseInterface, attrs: list[str]) -> None:
    """
    Replace tab completion list for ``dev`` with ``attrs``

    Parameters
    ----------
    dev : BaseInterface
        A single object implementing the tab completion features in
        pcdsdevices.interface.BaseInterface

    attrs : list[str]
        list of attributes to replace ``dev`` tablist with
    """
    for old_att in dir(dev):
        dev._tab.remove(old_att)

    for att in attrs:
        dev._tab.add(att)


def update_kind(dev: BaseInterface, attrs: dict) -> None:
    """
    Update the kind of components in ``dev``

    Parameters
    ----------
    dev : BaseInterface
        A single object implementing the tab completion features in
        pcdsdevices.interface.BaseInterface

    attrs : dict
        configuration for kind settings on ``dev``
    """
    for cpt, kind in attrs.items():
        k = getattr(Kind, kind, None)
        if not k:
            logger.debug(f'{kind} not a valid kind.')
            continue
        c = getattr(dev, cpt, None)
        if not c:
            logger.debug(f'Device {dev.name} has no component {cpt}')
            continue

        c.kind = k


# order of operations may matter.
mods = [
    ('tab_whitelist', update_whitelist),
    ('tab_blacklist', update_blacklist),
    ('replace_tablist', replace_tablist),
    ('kind', update_kind),
]


def configure_objects(
    obj_config: Union[str, Path],
    objs: utils.HelpfulNamespace,
    mod_list: list[Tuple[str, Callable]] = None
) -> utils.HelpfulNamespace:
    """
    Configure objects based on user provided settings.

    Parameters
    -----------
    obj_config : Pathlike
        Path to configuration yml file

    objs : HelpfulNamespsace
        All objects to be loaded into hutch-python

    mod_list : list[Tuple[str, Callable]]
        list of modifications to apply, formatted as a tuple of
        keys and corresponding functions

    Returns
    -------
    objs : HelpfulNamespace
        Modified objects
    """
    with utils.safe_load('user object configuration'):
        with open(obj_config, 'r') as f:
            cfg = yaml.safe_load(f)
        if mod_list is None:
            mod_list = mods

        for entry in cfg:
            # apply each valid configuration action
            for k, fn in mod_list:
                if k in cfg[entry]:
                    update_objs(objs, entry, cfg[entry][k], fn)
        return objs
