"""
This module defines options and settings the user may opt to change.
"""
from pcdsdevices.interface import set_engineering_mode


def set_default_options():
    set_engineering_mode(False)


def load_options(cache):
    cache(set_engineering_mode=set_engineering_mode)
    cache.doc(set_engineering_mode='Tab interface verbosity settings.')
    set_default_options()
