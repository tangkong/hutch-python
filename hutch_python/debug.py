"""
This module defines namespace mappings for debug utilities.
"""
from .log_setup import (debug_context, debug_mode, debug_wrapper,
                        set_console_level)


debug_tools = {
    'debug_console_level': set_console_level,
    'debug_mode': debug_mode,
    'debug_context': debug_context,
    'debug_wrapper': debug_wrapper,
    }


def load_debug(cache):
    cache(**debug_tools)
