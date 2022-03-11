import logging
from functools import wraps
from typing import Any, Callable

from bluesky import RunEngine
from bluesky.utils import RunEngineInterrupted

from .utils import HelpfulNamespace

logger = logging.getLogger(__name__)
registry = {}


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


class ImproperRunWrapperUse(RuntimeError):
    ...


def initialize_wrapper_namespaces(
    RE: RunEngine,
    plan_namespace: HelpfulNamespace,
    daq: Any,
) -> HelpfulNamespace:
    """
    Pick a RE/namespace set to use for register_plan.

    Populate the namespaces appropriately using the original contents of
    plan_namespace.

    This is used internally in hutch_python to prime future calls
    to register_plan.

    Parameters
    ----------
    RE : RunEngine
        The RunEngine to use.
    plan_namespace : HelpfulNamespace
        The namespace of normal bluesky plans.
    daq : Daq
        The daq object to use as another way to access daq plans.

    Returns
    -------
    re : HelpfulNamespace
        The namespace of run-wrapped scans.
    """
    registry['RE'] = RE
    registry['plan'] = plan_namespace
    registry['daq'] = daq
    registry['re'] = HelpfulNamespace()

    for name, plan in plan_namespace._get_items():
        logger.debug('Wrapping plan %s with run_engine_wrapper.', name)
        register_plan(plan=plan, name=name, initial=True)

    return registry['re']


def register_plan(plan: Callable, name: str, initial: bool = False) -> None:
    """
    Utility to add plans to the session namespaces.

    For this work properly, plan must be a generator function, not
    an open generator.

    The plan itself will be added to the main plans namespace,
    and a wrapped version will be added to the main run namespace.
    If the plan begins with the string "daq_" and does not clobber
    existing attributes on the daq object, it will also be grafted
    onto the daq instance with a truncated name.

    Parameters
    ----------
    plan : generator function
        A generator capable of being used in a bluesky scan.
    name : str
        The name to use as the attribute for our plan.
    initial : bool
        Whether or not this is the first-time load process.
        During the first load, we are reading from the original
        plan namespace, so we shouldn't be filling back to it.
    """
    if not initial:
        setattr(registry['plan'], name, plan)
    wrapped = run_engine_wrapper(registry['RE'], plan)
    logger.debug('Adding wrapped %s to re namespace', name)
    setattr(registry['re'], name, wrapped)
    daq = registry['daq']
    if daq is None:
        return
    if name.startswith('daq_'):
        short_name = name.removeprefix('daq_')
        if hasattr(daq, short_name):
            logger.warning(
                'Could not add %s scan to daq, name conflict!',
                short_name,
            )
        else:
            logger.debug(
                'Adding wrapped %s to the daq object as %s',
                name,
                short_name,
            )
            setattr(daq, short_name, wrapped)
            try:
                tab_helper = daq._tab
            except AttributeError:
                pass
            else:
                tab_helper.add(short_name)
