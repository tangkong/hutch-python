import logging
from functools import wraps

from bluesky import RunEngine

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
        setattr(runners, name, run_engine_wrapper(RE, plan))
    return runners


def run_engine_wrapper(RE: RunEngine, plan):
    @wraps(plan)
    def inner(*args, **kwargs):
        if not RE.state.is_idle:
            RE.abort()
        return RE(plan(*args, **kwargs))
    return inner
