import logging

import happi
from happi.loader import load_devices

try:
    # Optional import to skip for pip tests
    import lightpath
    from lightpath.config import beamlines
except ImportError:
    # Hold as None, check later to skip relevant bits
    lightpath = None
    # Hold as empty dict, will handle properly
    beamlines = {}

logger = logging.getLogger(__name__)


def get_happi_objs(db, hutch):
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
    # Find upstream items based on lightpath configuration
    beamline_conf = beamlines.get(hutch.upper())
    # Something strange is happening if there are no upstream items
    if not beamline_conf:
        logger.warning("Unable to find lightpath for %s",
                       hutch.upper())
        beamline_conf = {}
    # Add the complete hutch beamline
    beamline_conf[hutch.upper()] = {}
    # Base beamline
    for beamline, conf in beamline_conf.items():
        # Assume we want hutch items that are active
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
    dev_namespace = load_devices(*containers, pprint=False)
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
    if lightpath is None:
        raise RuntimeError(
            'Lightpath module unavailable or not initialized properly.'
        )
    # Load the happi Client
    client = happi.Client(path=db)
    # Allow the lightpath module to create a path
    lc = lightpath.LightController(client, endstations=[hutch.upper()])
    # Return the BeamPath object created by the LightController
    return lc.beamlines[hutch.upper()]
