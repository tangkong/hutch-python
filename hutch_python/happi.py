import inspect
import logging
from typing import Dict

import happi
from happi.loader import load_devices

try:
    import lightpath
    from lightpath import LightController
    from lightpath.config import beamlines
except ImportError:
    lightpath = None
    beamlines = None

logger = logging.getLogger(__name__)


def get_happi_objs(
    light_ctrl: LightController,
    endstation: str,
) -> Dict[str, happi.HappiItem]:
    """
    Get the relevant items for ``endstation`` from the happi database ``db``.

    This depends on a JSON ``happi`` database stored somewhere in the file
    system and handles setting up the ``happi.Client`` and querying the data
    base for items.

    Uses the paths found by the LightController, but does not use it to
    load the devices so we can do so ourselves and log load times.

    Parameters
    ----------
    light_ctrl: lightpath.LightController
        LightController instance constructe from the happi db

    hutch: ``str``
        Name of hutch

    Returns
    -------
    objs: ``dict``
        A mapping from item name to item
    """
    # Load the happi Client
    client = light_ctrl.client
    containers = list()

    dev_names = set()
    paths = light_ctrl.beamlines[endstation.upper()]
    for path in paths:
        dev_names.update(path)

    # gather happi items for each of these
    for name in dev_names:
        results = client.search(name=name)
        containers.extend(res.item for res in results)

    # also any device with the same beamline name
    # since lightpath only grabs lightpath-active devices
    beamlines = set(it.beamline for it in containers)

    for line in beamlines:
        # Assume we want hutch items that are active
        # items can be lightpath-inactive
        reqs = dict(beamline=line, active=True)
        results = client.search(**reqs)
        blc = [res.item for res in results
               if res.item.name not in dev_names]
        # Add the beamline containers to the complete list
        if blc:
            containers.extend(blc)
        else:
            logger.warning("No items found in database for %s",
                           line.upper())

    # Instantiate the devices needed
    sig = inspect.signature(load_devices)
    if "include_load_time" in sig.parameters:
        kwargs = dict(include_load_time=True, load_time_threshold=0.5)
    else:
        kwargs = {}
    dev_namespace = load_devices(*containers, pprint=False, **kwargs)
    return dev_namespace.__dict__


def get_lightpath(db, hutch) -> LightController:
    """
    Create a ``lightpath.LightController`` from relevant ``happi`` objects.

    Parameters
    ----------
    db: ``str``
        Path to database

    hutch: ``str``
        Name of hutch

    Returns
    -------
    path: ``lightpath.LightController``
        Object that contains the a representation of the facility graph.  Can
        be used to access a ``BeamPath``, which provides a convenient way to
        visualize all the devices that may block the beam on the way to the
        interaction point.
    """
    if None in (lightpath, beamlines):
        logger.warning('Lightpath module is not available.')
        return None
    # Load the happi Client
    client = happi.Client(path=db)
    # Allow the lightpath module to create a path
    lc = lightpath.LightController(client, endstations=[hutch.upper()])
    # Return paths (names only) seen by the LightController
    # avoid loding the devices so hutch-python can keep track of it
    return lc
