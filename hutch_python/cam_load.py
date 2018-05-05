"""
Load Detector objects based on a camviewer config file
"""
import logging

from pcdsdevices.areadetector.detectors import PCDSDetector

logger = logging.getLogger(__name__)


def read_camviewer_cfg(filename):
    """
    Read camviewer.cfg file and create detector objects.

    Parameters
    ----------
    filename: ``str``
        Full path to the camviewer.cfg file.

    Returns
    -------
    dict: ``{str: PCDSDetector}``
        Each detector object, indexed by name.
    """
    with open(filename, 'r') as f:
        lines = f.readlines()

    return interpret_lines(lines)


def interpret_lines(lines):
    """
    Create detector object from string lines of a camviewer.cfg file.

    Parameters
    ----------
    lines: ``list of str``
        The python strings for each line of the config file

    Returns
    -------
    dict: ``{str: PCDSDetector}``
        Each detector object, indexed by name.
    """
    objs = {}

    for line in lines:
        line = line.strip()
        if not line or line[0] == '#':
            continue

        parts = line.split(',')
        parts = [p.strip() for p in parts]

        if parts[0].startswith('include'):
            try:
                objs.update(read_camviewer_cfg(parts[0].split(' ')[1]))
            except IndexError:
                err = 'Malformed include line "%s" in camviewer cfg, skipping.'
                logger.error(err, line)
        else:
            try:
                new_obj = build_cam(*parts)
                objs[new_obj.name] = new_obj
                logger.debug('Loaded %s', new_obj.name)
            except UnsupportedConfig as exc:
                logger.debug('Skip non area detector cam %s',
                             exc.name, exc_info=True)
            except MalformedConfig as exc:
                err = 'Skip malformed config for cam %s'
                logger.error(err, exc.name)
                logger.debug(err, exc.name, exc_info=True)
            except TypeError:
                err = 'Malformed cam line "%s" in camviewer cfg, skipping.'
                logger.error(err, line)
                logger.debug(err, line, exc_info=True)

    return objs


def build_cam(cam_type, pv_info, evr, name, *args):
    """
    Create a single detector object, using camviewer.cfg information.

    Paramaters
    ----------
    cam_type: ``str``
        The first element in the camviewer config line, determines whether or
        not we have a detector class for the camera.

    pv_info: ``str``
        Second element in the line, determines which PVs to use.

    evr: ``str``
        Third element in the line, determines the EVR PVs. This is currently
        not used.

    name: ``str``
        Fourth element in th eline, determines the object's name.

    *args:
        Optional arguments that are unused.

    Returns
    -------
    cam: ``PCDSDetector``
    """
    if not cam_type.startswith('GE'):
        raise UnsupportedConfig('Only cam type GE (area detector) supported.',
                                name=name)

    if not pv_info or not name:
        raise MalformedConfig(name=name)

    pv_info = pv_info.split(';')
    try:
        detector_prefix = pv_info[1]
    except IndexError:
        logger.debug('detector_prefix missing from pv_info %s', pv_info)
        # Not provided in config, guess from image base
        detector_prefix = ':'.join(pv_info[0].split(':')[:-1])

    return PCDSDetector(detector_prefix, name=name)


class UnsupportedConfig(Exception):
    def __init__(self, message=None, name=None):
        self.message = message or 'Unsupported config'
        self.name = name


class MalformedConfig(Exception):
    def __init__(self, message=None, name=None):
        self.message = message or 'Malformed config'
        self.name = name
