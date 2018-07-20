import logging
from importlib import import_module
from types import SimpleNamespace

from .utils import safe_load

logger = logging.getLogger(__name__)


def get_exp_objs(proposal, run):
    """
    Load the correct experiment module.

    This will import User from ``experiments.{propsal}{run}``
    and create ``User()``, storing it as ``x``.

    Parameters
    ----------
    proposal: ``str``
        The proposal name, e.g. ``lp56``. This will be forced to
        lowercase for the import.

    run: ``str`` or ``int``
        The run number, e.g. 16

    Returns
    -------
    user: ``object`` or ``SimpleNamespace``
        Either the user's class instantiated or a blank namespace for other
        experiment-specific objects to be attached to.
    """
    logger.debug('get_exp_objs(%s, %s)', proposal, run)
    expname = proposal.lower() + str(run)
    module_name = 'experiments.' + expname
    with safe_load(expname):
        try:
            module = import_module(module_name)
            return module.User()
        except ImportError as exc:
            if module_name in exc.msg:
                logger.info('Skip missing experiment file %s.py', expname)
            else:
                raise
    return SimpleNamespace()


def split_expname(expname, hutch=None):
    """
    Give an experiment name, split out the proposal and the run number.

    This is used in the split form because certain applications take the two
    separately.

    Parameters
    ----------
    expname: ``str``
        The name of an experiment, e.g. xppx0112

    hutch: ``str``, optional
        If provided, and we find the hutch string in the expname, we'll strip
        it out.

    Returns
    -------
    proposal, run: ``tuple``, (``str``, ``str``)
        e.g. ('x01', '12')
    """
    expname = expname.lower()
    if hutch is not None:
        hutch = hutch.lower()
        if expname.startswith(hutch):
            expname = expname[len(hutch):]
    proposal = expname[:-2]
    run = expname[-2:]
    logger.debug('split expname %s into proposal=%s, run=%s',
                 expname, proposal, run)
    return proposal, run
