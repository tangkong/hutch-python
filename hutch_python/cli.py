"""
This module defines the command-line interface arguments for the
``hutch-python`` script. It also provides utilities that are only used at
startup.
"""
from pathlib import Path
from traitlets.config import Config
import argparse
import logging
import os

from IPython import start_ipython
from cookiecutter.main import cookiecutter
from pcdsdaq.sim import set_sim_mode as set_daq_sim

from .constants import CONDA_BASE, DIR_MODULE
from .load_conf import load
from .log_setup import (setup_logging, set_console_level, debug_mode,
                        debug_context, debug_wrapper)

logger = logging.getLogger(__name__)
opts_cache = {}

# Define the parser
parser = argparse.ArgumentParser(prog='hutch-python',
                                 description='Launch LCLS Hutch Python')
parser.add_argument('--cfg', required=False, default=None,
                    help='Configuration yaml file')
parser.add_argument('--exp', required=False, default=None,
                    help='Experiment number override')
parser.add_argument('--debug', action='store_true', default=False,
                    help='Start in debug mode')
parser.add_argument('--sim', action='store_true', default=False,
                    help='Run with simulated DAQ')
parser.add_argument('--create', action='store', default=False,
                    help='Create a new hutch deployment')
parser.add_argument('script', nargs='?',
                    help='Run a script instead of running interactively')

# Append to module docs
__doc__ += '\n::\n\n    ' + parser.format_help().replace('\n', '\n    ')


def main():
    """
    Do the full hutch-python launch sequence.

    Parses the user's cli arguments and distributes them as needed to the
    setup functions.
    """
    # Parse the user's arguments
    args = parser.parse_args()

    # Set up logging first
    if args.cfg is None:
        log_dir = None
    else:
        log_dir = os.path.join(os.path.dirname(args.cfg), 'logs')
    setup_logging(dir_logs=log_dir)

    # Debug mode next
    if args.debug:
        debug_mode(True)

    # Do the first log message, now that logging is ready
    logger.debug('cli starting with args %s', args)

    # Options that mean skipping the python environment
    if args.create:
        hutch = args.create
        envs_dir = CONDA_BASE / 'envs'
        if envs_dir.exists():
            # Pick most recent pcds release in our common env
            base = str(CONDA_BASE)
            path_obj = sorted(envs_dir.glob('pcds-*'))[-1]
            env = path_obj.name
        else:
            # Fallback: pick current env
            base = str(Path(os.environ['CONDA_EXE']).parent.parent)
            env = os.environ['CONDA_DEFAULT_ENV']
        logger.info(('Creating hutch-python dir for hutch %s using'
                     ' base=%s env=%s'), hutch, base, env)
        cookiecutter(str(DIR_MODULE / 'cookiecutter'), no_input=True,
                     extra_context=dict(base=base, env=env, hutch=hutch))
        return

    # Now other flags
    if args.sim:
        set_daq_sim(True)

    # Save whether we are an interactive session or a script session
    opts_cache['script'] = args.script

    # Load objects based on the configuration file
    objs = load(cfg=args.cfg, args=args)

    # Add cli debug tools
    objs['debug_console_level'] = set_console_level
    objs['debug_mode'] = debug_mode
    objs['debug_context'] = debug_context
    objs['debug_wrapper'] = debug_wrapper

    script = opts_cache.get('script')
    if script is None:
        ipy_config = Config()
        # Important Utilities
        ipy_config.InteractiveShellApp.extensions = [
            'hutch_python.ipython_log',
            'hutch_python.bug'
        ]
        # Matplotlib setup if we have a screen
        if os.getenv('DISPLAY'):
            ipy_config.InteractiveShellApp.matplotlib = 'qt5'
        else:
            logger.warning('No DISPLAY environment variable detected. '
                           'Methods that create graphics will not '
                           'function properly.')
        # Finally start the interactive session
        start_ipython(argv=['--quick'], user_ns=objs, config=ipy_config)
    else:
        # Instead of setting up ipython, run the script with objs
        with open(script) as fn:
            code = compile(fn.read(), script, 'exec')
            exec(code, objs, objs)
