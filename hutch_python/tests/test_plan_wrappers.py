import logging
from typing import Any, Callable

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import null, pause
from bluesky.plans import scan
from bluesky.utils import RunEngineInterrupted
from ophyd.sim import motor

from hutch_python.plan_wrappers import (ImproperRunWrapperUse, PlanWrapper,
                                        RunEngineWrapper,
                                        initialize_wrapper_namespaces,
                                        register_plan, registry)
from hutch_python.utils import HelpfulNamespace

logger = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def RE() -> RunEngine:
    return RunEngine(call_returns_result=True)


@pytest.fixture(scope='function')
def run_scan(RE: RunEngine) -> Callable:
    return RunEngineWrapper(scan, RE)


def do_standard_check(run_scan: Callable):
    motor.set(5)
    result = run_scan([], motor, 0, 10, 11)
    assert result.exit_status == 'success'
    assert motor.position == 10
    return result


def test_plan_wrapper_runs(RE):
    logger.debug('test_plan_wrapper_runs')
    plan = PlanWrapper(scan)

    def thin_wrapper(*args, **kwargs):
        return RE(plan(*args, **kwargs))

    do_standard_check(thin_wrapper)


def test_run_engine_wrapper_runs(run_scan: Callable):
    logger.debug('test_run_engine_wrapper_runs')
    do_standard_check(run_scan)


def test_run_engine_wrapper_from_interrupt(
    RE: RunEngine,
    run_scan: Callable,
):
    logger.debug('test_run_engine_wrapper_from_interrupt')

    def interrupt_plan():
        yield from null()
        yield from pause()
        yield from null()

    with pytest.raises(RunEngineInterrupted):
        RE(interrupt_plan())
    assert not RE.state.is_idle

    do_standard_check(run_scan)


def test_run_engine_wrapper_nested_bad(
    RE: RunEngine,
    run_scan: Callable,
):
    logger.debug('test_run_engine_wrapper_nested_bad')

    def bad_plan():
        yield from null()
        run_scan()
        yield from null()

    with pytest.raises(ImproperRunWrapperUse):
        RE(bad_plan())


@pytest.fixture(scope='function')
def plan_namespace() -> HelpfulNamespace:
    return HelpfulNamespace(
        scan=scan,
        daq_scan=scan,
    )


@pytest.fixture(scope='function')
def wrapper_registry(
    RE: RunEngine,
    plan_namespace: HelpfulNamespace,
) -> dict[str, Any]:
    daq = HelpfulNamespace()
    registry.clear()
    initialize_wrapper_namespaces(
        RE=RE,
        plan_namespace=plan_namespace,
        daq=daq,
    )
    yield registry
    registry.clear()


def test_run_scan_namespace(wrapper_registry: dict[str, Any]):
    logger.debug('test_run_scan_namespace')
    run_namespace = wrapper_registry['re']
    do_standard_check(run_namespace.scan)


def test_daq_scan_object(wrapper_registry: dict[str, Any]):
    logger.debug('test_daq_scan_object')
    run_namespace = wrapper_registry['re']
    daq_object = wrapper_registry['daq']
    assert run_namespace.daq_scan is daq_object.scan
    do_standard_check(daq_object.scan)


def test_registry(wrapper_registry: dict[str, Any]):
    logger.debug('test_registry')
    plan_namespace = wrapper_registry['plan']
    run_namespace = wrapper_registry['re']
    daq_object = wrapper_registry['daq']

    def some_random_plan(*args, **kwargs):
        yield from scan(*args, **kwargs)

    with pytest.raises(AttributeError):
        plan_namespace.some_random_plan

    with pytest.raises(AttributeError):
        run_namespace.some_random_plan

    register_plan(plan=some_random_plan, name='some_random_plan')
    plan_namespace.some_random_plan

    do_standard_check(run_namespace.some_random_plan)

    register_plan(plan=some_random_plan, name='daq_super_plan')
    plan_namespace.daq_super_plan

    do_standard_check(run_namespace.daq_super_plan)
    do_standard_check(daq_object.super_plan)


def test_plan_wrapper_invalid_args():
    logger.debug('test_plan_wrapper_invalid_args')
    with pytest.raises(TypeError):
        PlanWrapper(None)

    with pytest.raises(TypeError):
        PlanWrapper(scan([], motor, 0, 10, 11))


def test_double_wrapper():
    logger.debug('test_double_wrapper')
    wrapper_one = PlanWrapper(scan)
    wrapper_two = PlanWrapper(wrapper_one)
    assert wrapper_one.plan is scan
    assert wrapper_two.plan is scan
