import logging
from pathlib import Path
from typing import Callable, Union

import yaml
from ophyd import Device, Kind
from pcdsdevices.interface import BaseInterface

from . import utils

logger = logging.getLogger(__name__)


def update_objs(
    obj_ns: utils.HelpfulNamespace,
    entry: str,
    attrs: dict,
    fn: Callable[[BaseInterface, Union[dict, list[str]]], None],
) -> bool:
    """
    Helper function for updating object namespaces
    obj_ns is a HelpfulNamespace, which may include other
    HelpfulNamespace's.  As a result this must be semi-recursive.

    Parameters
    ----------
    obj_ns : HelpfulNamespace
        Namespace of all objects

    entry : str
        Entry in obj_conf yaml. Name of device or class of devices to edit.

    attrs : list[str]
        List of attributes to add to whitelist

    fn : Callable[[BaseInterface, dict], None]
        A function that applies a change to a singular device

    Returns
    -------
    bool
        True if modification was applied, False otherwise

    """
    dev = getattr(obj_ns, entry, None)
    if dev:  # look for explicit device
        try:
            fn(dev, attrs)
            # if we match a specific device, there should be no dupes
            return True
        except AttributeError:
            # if class is in namespace, can be misinterpreted as a device
            # currently covered by AttributeError, might not be futureproof
            logger.warning(f'{dev} cannot be modified with {fn.__name__}')

    # look for devices with class
    found_ns = False
    found_match = False
    found = False
    for dev in obj_ns:
        if isinstance(dev, utils.HelpfulNamespace):
            found_ns = update_objs(dev, entry, attrs, fn)
        # a poor-man's type check, in an effort to avoid importing
        # every device type again
        if entry == type(dev).__name__:
            fn(dev, attrs)
            found_match = True

        # need to keep found conditions separate, and not overwrite them
        # with each iter. (could search through ns without finding a match)
        if found_ns or found_match:
            found = True

    return found


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


def update_kind(dev: Device, attrs: dict) -> None:
    """
    Update the kind of components in ``dev``.  If a key matches the
    device name, the top-level device kind will be modified.

    Parameters
    ----------
    dev : ophyd.Device
        A single Ophyd Device with Kind attributes

    attrs : dict
        configuration for kind settings on ``dev``
    """
    for cpt, kind in attrs.items():
        kind = getattr(Kind, kind, None)
        if kind is None:
            logger.debug(f'{kind} not a valid kind.')
            continue

        if cpt == dev.name:
            dev.kind = kind
            continue

        c = getattr(dev, cpt, None)
        if not c:
            logger.debug(f'Device {dev.name} has no component {cpt}')
            continue

        c.kind = kind


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
    mod_list: list[tuple[str, Callable]] = None
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
        with open(obj_config) as f:
            cfg = yaml.safe_load(f)
        if mod_list is None:
            mod_list = mods

        for entry in cfg:
            # apply each valid configuration action
            found = False
            for k, fn in mod_list:
                if k in cfg[entry]:
                    found = update_objs(objs, entry, cfg[entry][k], fn)

            # warn if device not found
            if not found:
                logger.warning(
                    f'Entry ({entry}) not found in current session, '
                    f'cannot apply changes ({fn.__name__}) '
                )
        return objs
