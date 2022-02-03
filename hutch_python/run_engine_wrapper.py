import logging
from functools import wraps
from typing import Callable

from bluesky import RunEngine
from bluesky.utils import RunEngineInterrupted

from .utils import HelpfulNamespace

logger = logging.getLogger(__name__)


def run_scan_namespace(
    RE: RunEngine,
    plan_namespace: HelpfulNamespace,
) -> HelpfulNamespace:
    """
    Create a namespace with shortcuts to run every input plan on the RE.

    This namespace came about because users were creating this sort of
    thing themselves and losing time over getting the specifics
    exactly right. It's also quite a lot of overhead to manually wrap
    every scan that you'd want to use.

    This is an alternative to ipython magics-based plan runners.

    Parameters
    ----------
    RE : RunEngine
        The run engine to use in the shortcut wrappers.
    plan_namespace : HelpfulNamespace
        A HelpfulNamespace containing all the plans to wrap.

    Returns
    -------
    run_scan_namespace:
        A mirror of plan_namespace with every plan wrapped for quick calls
        from the RunEngine.
    """
    runners = HelpfulNamespace()
    for name, plan in plan_namespace._get_items():
        logger.debug('Wrapping plan %s with run_engine_wrapper.', name)
        setattr(runners, name, run_engine_wrapper(RE, plan))
    return runners


def run_engine_wrapper(RE: RunEngine, plan: Callable) -> Callable:
    """
    Wrap a plan to automatically include the RE() call.

    For this work properly, plan must be a generator function, not
    an open generator.

    Note that this changes the nature of the plan. What was
    originally a generator function that takes no actions on its own
    becomes a function that directly moves hardware and orchestrates
    data collection.

    This will also stop the previous run engine run if the run engine
    has not been cleaned up.
    This can happen if the previous scan was interrupted, say, by
    ctrl+c and none of RE.resume, RE.abort, RE.stop, or RE.halt
    have been called.
    RE.stop is used here because it cleans up the previous run
    without making a large logger exception text.

    Parameters
    ----------
    RE : RunEngine
        The run engine to call this plan with.
    plan : generator function
        A generator capable of being used in a bluesky scan.

    Returns
    -------
    runner : function
        A function that runs the scan directly, including moving
        hardware and orchestrating data collection.
    """
    @wraps(plan)
    def run_scan(*args, **kwargs):
        if not RE.state.is_idle:
            logger.info('Previous scan still open, calling stop')
            RE.stop()
        try:
            return RE(plan(*args, **kwargs))
        except RunEngineInterrupted as exc:
            print(exc)
    return run_scan
