"""
Load Detector objects based on a camviewer config file
"""
import logging

from pcdsdevices.areadetector.detector import PCDSDetector

logger = logging.getLogger(__name__)


def read_cfg(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    return interpret_lines(lines)


def interpret_lines(lines):
    objs = {}

    for line in lines:
        line = line.strip()
        if not line or line[0] == '#':
            continue

        parts = line.split(',')
        parts = [p.strip() for p in parts]

        if parts[0] == 'include':
            try:
                objs.update(read_cfg(parts[1]))
            except IndexError:
                err = 'Malformed include line "%s" in camviewer cfg, skipping.'
                logger.error(err, line)
        else:
            try:
                new_obj = build_cam(*parts)
                objs[new_obj.name] = new_obj
            except UnsupportedConfig as exc:
                logger.debug('Skip non area detector cam %s',
                             exc.name, exc_info=True)
            except MalformedConfig as exc:
                err = 'Skip malformed config for cam %s'
                logger.error(err, exc.name)
                logger.debug(err, exc.name, exc_info=True)

    return objs


def build_cam(cam_type, pv_info, evr, name, lens=None)
    if not cam_type.startswith('RE'):
        raise UnsupportedConfig('Only cam type GE (area detector) supported.',
                                name=name)

    pv_info = pv_info.split(';')
    try:
        try:
            detector_prefix = pv_info[1]
        except IndexError:
            logger.debug('detector_prefix missing from pv_info %s', pv_info)
            # Not provided in config, guess from image base
            detector_prefix = ':'.join(pv_info[0].split(':')[:-1])
    except Exception:
        raise MalformedConfig(name=name)

    return PCDSDetector(detector_prefix, name=name)


class UnsupportedConfig(Exception):
    def __init__(self, message=None, name=None):
        self.message = message or 'Unsupported config'
        self.name = name


class MalformedConfig(Exception):
    def __init__(self, message=None, name=None):
        self.message = message or 'Malformed config'
        self.name = name
