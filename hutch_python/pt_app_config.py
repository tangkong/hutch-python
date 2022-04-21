"""
This file defines an ipython extension to configure the terminal app.
Currently this configures:
- disabling the Ctrl+\\ keybind
"""

import logging

from prompt_toolkit.keys import Keys

from .utils import safe_load

logger = logging.getLogger(__name__)


def load_ipython_extension(ipython):
    # Unbind Ctrl+\\
    with safe_load('disable ctrl+\\'):
        ipython.pt_app.key_bindings.remove(
            Keys.ControlBackslash
        )
