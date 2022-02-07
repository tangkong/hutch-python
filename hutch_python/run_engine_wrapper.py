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
        if RE.state.is_running:
            raise ImproperRunWrapperUse(
                'There is already a scan in progress! Cannot start a new one! '
                'Either we are improperly nested inside another scan or there '
                'are multiple threads trying to use the same RE instance.'
            )
        if not RE.state.is_idle:
            logger.info('Previous scan still open, calling stop')
            RE.stop()
        try:
            return RE(plan(*args, **kwargs))
        except RunEngineInterrupted as exc:
            print(exc)
    return run_scan


registry = {}


def register_namespace(
    RE: RunEngine,
    plan_namespace: HelpfulNamespace,
    run_namespace: HelpfulNamespace,
) -> None:
    """
    Pick a RE/namespace set to use for register_plan.

    This is used internally in hutch_python to prime future calls
    to register_plan.

    Parameters
    ----------
    RE : RunEngine
        The RunEngine to use.
    plan_namespace : HelpfulNamespace
        The namespace of normal bluesky plans.
    run_namespace : HelpfulNamespace
        The namespace of run-engine-wrapped plans.
    """
    registry['RE'] = RE
    registry['plan'] = plan_namespace
    registry['run'] = run_namespace


def register_plan(plan: Callable, name: str) -> None:
    """
    Utility to add user-defined plans to the session namespaces.

    For this work properly, plan must be a generator function, not
    an open generator.

    The plan itself will be added to the main plans namespace,
    and a wrapped version will be added to the main run namespace.

    Parameters
    ----------
    plan : generator function
        A generator capable of being used in a bluesky scan.
    name : str
        The name to use as the attribute for our plan.
    """
    setattr(registry['plan'], name, plan)
    setattr(
        registry['run'],
        name,
        run_engine_wrapper(registry['RE'], plan),
    )


class ImproperRunWrapperUse(RuntimeError):
    ...
