"""
Utilities for getting relevant environment information.
"""
from __future__ import annotations

import logging
import os
import os.path

import pkg_resources

logger = logging.getLogger(__name__)

_dev_ignore_list = ['x86_64-rhel7-opt', 'x86_64-linux-opt']


def log_env() -> None:
    """Collect environment information and log at appropriate levels."""
    dev_pkgs = get_standard_dev_pkgs()
    if dev_pkgs:
        logger.debug(
            'Using conda env %s with dev packages %s',
            get_conda_env_name(),
            ', '.join(sorted(dev_pkgs)),
        )
    else:
        logger.debug(
            'Using conda env %s with no dev packages',
            get_conda_env_name(),
        )
    logger.debug(dump_env())


def dump_env() -> list[str]:
    """
    Get all packages nad versions from the current environment.
    conda list is slow, use pkg_resources instead
    this might miss dev overrides
    """
    return sorted(str(pkg) for pkg in pkg_resources.working_set)


def get_conda_env_name() -> str:
    """Get the name of the conda env, or empty string if none."""
    env_dir = os.environ.get('CONDA_PREFIX', '')
    return os.path.basename(env_dir)


def get_standard_dev_pkgs() -> set[str]:
    """Check the standard dev package locations for hutch-python"""
    pythonpath = os.environ.get('PYTHONPATH', '')
    if not pythonpath:
        return set()
    pkg_names = set()
    for part in pythonpath.split(':'):
        if any([(s in part) for s in _dev_ignore_list]) or (not part):
            continue
        pkg_names.add(os.path.basename(os.path.dirname(part)))
    return pkg_names


def get_env_info() -> str:
    """ Collect environment information and format as banner """
    conda_ver = get_conda_env_name()
    dev_pkgs = get_standard_dev_pkgs()

    banner = (
        'Environment Information\n'
        f'  Conda Environment: {conda_ver}\n'
        f'  Development Packages: {" ".join(dev_pkgs)}'
    )

    return banner
