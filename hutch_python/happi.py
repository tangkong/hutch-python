import inspect
import logging

import happi
from happi.loader import load_devices

try:
    import lightpath
    from lightpath.config import beamlines
except ImportError:
    lightpath = None
    beamlines = None

logger = logging.getLogger(__name__)


def get_happi_objs(db, beampath, hutch):
    """
    Get the relevant items for ``hutch`` from ``db``.

    This depends on a JSON ``happi`` database stored somewhere in the file
    system and handles setting up the ``happi.Client`` and querying the data
    base for items.

    Parameters
    ----------
    db: ``str``
        Path to database

    hutch: ``str``
        Name of hutch

    Returns
    -------
    objs: ``dict``
        A mapping from item name to item
    """
    # Load the happi Client
    client = happi.Client(path=db)
    containers = list()

    # find upstream beamlines based on devices in beampath
    # should be data in 'beamline' happi key
    lines = set((dev.md.beamline for dev in beampath.devices))
    lines.add(hutch.upper())

    for beamline in lines:
        # Assume we want hutch items that are active
        # items can be lightpath-inactive
        reqs = dict(beamline=beamline, active=True)
        results = client.search(**reqs)
        blc = [res.item for res in results]
        # Add the beamline containers to the complete list
        if blc:
            containers.extend(blc)
        else:
            logger.warning("No items found in database for %s",
                           beamline.upper())
    # Instantiate the devices needed
    sig = inspect.signature(load_devices)
    if "include_load_time" in sig.parameters:
        kwargs = dict(include_load_time=True, load_time_threshold=0.5)
    else:
        kwargs = {}
    dev_namespace = load_devices(*containers, pprint=False, **kwargs)
    return dev_namespace.__dict__


def get_lightpath(db, hutch):
    """
    Create a lightpath from relevant ``happi`` objects.

    Parameters
    ----------
    db: ``str``
        Path to database

    hutch: ``str``
        Name of hutch

    Returns
    -------
    path: ``lightpath.BeamPath``
        Object that provides a convenient way to visualize all the devices
        that may block the beam on the way to the interaction point.
    """
    if None in (lightpath, beamlines):
        logger.warning('Lightpath module is not available.')
        return None
    # Load the happi Client
    client = happi.Client(path=db)
    # Allow the lightpath module to create a path
    lc = lightpath.LightController(client, endstations=[hutch.upper()])
    # Return the BeamPath object created by the LightController
    return lc.active_path(hutch.upper())
