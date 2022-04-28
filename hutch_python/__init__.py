import logging

from . import _version

logger = logging.getLogger(__name__)

__version__ = _version.get_versions()['version']
