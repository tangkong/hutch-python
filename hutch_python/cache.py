"""
This module is responsible for accumulating all loaded objects and making sure
they are available in the ``xxx.db`` virtual module. It is used extensively in
`load_conf.load_conf`.
"""
import datetime
import logging
import sys
import textwrap
from importlib import import_module
from pathlib import Path

from .utils import HelpfulNamespace

logger = logging.getLogger(__name__)


class LoadCache:
    """
    Class that accumulates objects in a virtual module.

    This virtual module can be imported from as if it were a normal module.

    Parameters
    ----------
    module: ``str``
        Name of the virtual module to create. If the module has the same
        name as a real module, the real module will be masked.

    hutch_dir: ``Path``, optional
        This allows us to write a ``db.txt`` file to let the user know what
        objects get imported.

    **objs: kwargs
        Initial objects to place into the namespace

    Attributes
    ----------
    objs: `HelpfulNamespace`
        This is a namespace containing all the objects that have been attached
        to the ``LoadCache``.
    """
    def __init__(self, module, hutch_dir=None, **objs):
        self.objs = HelpfulNamespace(**objs)
        self.hutch_dir = hutch_dir
        self.module = module
        self.spoof_module(module)
        self.spoof_module('hutch_python.db')

    def spoof_module(self, module_name):
        """
        Create a fake module that is actually self.objs
        """
        # Check for real module that it needs to be slipped into
        module_parts = module_name.split('.')
        parent = '.'.join(module_parts[:-1])
        if parent:
            try:
                parent_module = import_module(parent)
                setattr(parent_module, module_parts[-1], self.objs)
            except ImportError:
                logger.debug('Skip patching parent module %s, does not import',
                             parent, exc_info=True)

        # Place it here so it looks like we've already imported it
        sys.modules[module_name] = self.objs

    def __call__(self, **objs):
        """
        Add objects to the namespace.

        Parameters
        ----------
        **objs: kwargs
            The key will is the namespace-accessible name, and the object
            is the object we are adding.
        """
        self.objs.__dict__.update(**objs)

    def write_file(self):
        """
        Write a ``db.txt`` file in the hutch's directory. This file informs
        the user which objects get loaded by ``hutch-python``.
        """
        if self.hutch_dir is not None:
            parts = self.module.split('.')
            parts[-1] = parts[-1] + '.txt'
            db_path = self.hutch_dir / Path('/'.join(parts))
            text = (header.format(parts[0])
                    + body.format(datetime.datetime.now()))
            for name, obj in self.objs.__dict__.items():
                text += '{:<20} {}\n'.format(name, obj.__class__)
            if not db_path.exists():
                db_path.touch()
                db_path.chmod(0o666)
            with db_path.open('w') as f:
                f.write(text)

    def doc(self, **docs):
        """
        Add docstrings to the cached objects.

        Parameters
        ----------
        **objs: kwargs
            The key should be the object name, the value should be
            documentation about that object and why it is included.
        """
        for key, value in docs.items():
            obj = self.objs[key]
            if obj.__doc__:
                obj.__doc__ = value + '\n' + textwrap.dedent(obj.__doc__)
            else:
                obj.__doc__ = value


# For writing the files
header = """
The objects referenced in this file are populated by the {0}python\n
initialization. If you wish to use devices from this file, import\n
them from {0}.db after calling the {0}python startup script.\n\n
"""
body = ('hutch-python last loaded on {}\n'
        'with the following objects:\n\n')
