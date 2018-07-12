"""
Load Detector objects based on a camviewer config file
"""
import logging
from functools import partial
from multiprocessing.pool import ThreadPool
from multiprocessing import cpu_count

from .constants import SUCCESS_LEVEL

from pcdsdevices.areadetector.detectors import PCDSDetector

logger = logging.getLogger(__name__)
logger.success = partial(logger.log, SUCCESS_LEVEL)


def read_camviewer_cfg(filename):
    """
    Read camviewer.cfg file and create detector objects.

    Parameters
    ----------
    filename: ``str``
        Full path to the camviewer.cfg file.

    Returns
    -------
    objs: ``{str: PCDSDetector}``
        Each detector object, indexed by name.
    """
    info = interpret_cfg(filename)
    return load_cams(info)


def interpret_cfg(filename):
    """
    Read camviewer.cfg file and interpret lines

    Parameters
    ----------
    filename: ``str``
        Full path to the camviewer.cfg file.

    Returns
    -------
    info: ``list of str``
        Valid inputs for build_cam
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
    info: ``list of list str``
        Valid inputs for build_cam
    """
    info = []

    for line in lines:
        line = line.strip()
        if not line or line[0] == '#':
            continue

        logger.debug(line)
        parts = line.split(',')
        parts = [p.strip() for p in parts]

        if parts[0].startswith('include'):
            try:
                inc = interpret_cfg(parts[0].split(' ')[1])
                info.extend(inc)
            except IndexError:
                err = 'Malformed include line "%s" in camviewer cfg, skipping.'
                logger.error(err, line)
                logger.debug(err, line, exc_info=True)
        else:
            info.append(parts)

    return info


def load_cams(info):
    """
    Create detector object from string lines of a camviewer.cfg file.

    Parameters
    ----------
    info: ``list of list of str``
        Valid inputs for build_cam

    Returns
    -------
    objs: ``{str: PCDSDetector}``
        Each detector object, indexed by name.
    """
    objs = {}
    logger.debug(info)
    pool = ThreadPool(cpu_count()-1)
    obj_list = pool.map(build_and_log, info)
    for obj in obj_list:
        if obj is not None:
            objs[obj.name] = obj
    return objs


def build_and_log(info_part):
    try:
        obj = build_cam(*info_part)
        logger.success('Loaded %s', obj.name)
        return obj
    except UnsupportedConfig as exc:
        logger.debug('Skip non area detector cam %s',
                     exc.name, exc_info=True)
    except MalformedConfig as exc:
        err = 'Skip malformed config %s'
        logger.error(err, info_part)
        logger.debug(err, info_part, exc_info=True)
    except TypeError:
        err = 'Malformed config %s in camviewer cfg, skipping.'
        logger.error(err, info_part)
        logger.debug(err, info_part, exc_info=True)
    except Exception:
        err = ('Error loading config %s in camviewer cfg. IOC '
               'probably down, skipping.')
        logger.error(err, info_part)
        logger.debug(err, info_part, exc_info=True)


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
