from typing import Callable

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import null, pause
from bluesky.plans import scan
from bluesky.utils import RunEngineInterrupted
from ophyd.sim import motor

from hutch_python.run_engine_wrapper import (
    register_namespace, register_plan, run_engine_wrapper, run_scan_namespace)
from hutch_python.utils import HelpfulNamespace


@pytest.fixture(scope='function')
def RE() -> RunEngine:
    return RunEngine(call_returns_result=True)


@pytest.fixture(scope='function')
def run_scan(RE: RunEngine) -> Callable:
    return run_engine_wrapper(RE, scan)


def do_standard_check(run_scan: Callable):
    motor.set(5)
    result = run_scan([], motor, 0, 10, 11)
    assert result.exit_status == 'success'
    assert motor.position == 10
    return result


def test_run_engine_wrapper_runs(run_scan: Callable):
    do_standard_check(run_scan)


def test_run_engine_wrapper_from_interrupt(
    RE: RunEngine,
    run_scan: Callable,
):
    def interrupt_plan():
        yield from null()
        yield from pause()
        yield from null()

    with pytest.raises(RunEngineInterrupted):
        RE(interrupt_plan())
    assert not RE.state.is_idle

    do_standard_check(run_scan)


@pytest.fixture(scope='function')
def plan_namespace():
    return HelpfulNamespace(scan=scan)


@pytest.fixture(scope='function')
def run_namespace(RE: RunEngine, plan_namespace: HelpfulNamespace):
    return run_scan_namespace(
        RE=RE,
        plan_namespace=plan_namespace,
    )


def test_run_scan_namespace(run_namespace: HelpfulNamespace):
    do_standard_check(run_namespace.scan)


def test_registry(
    RE: RunEngine,
    plan_namespace: HelpfulNamespace,
    run_namespace: HelpfulNamespace,
):
    register_namespace(
        RE=RE,
        plan_namespace=plan_namespace,
        run_namespace=run_namespace,
    )

    def some_random_plan(*args, **kwargs):
        yield from scan(*args, **kwargs)

    with pytest.raises(AttributeError):
        plan_namespace.some_random_plan

    with pytest.raises(AttributeError):
        run_namespace.some_random_plan

    register_plan(plan=some_random_plan, name='some_random_plan')
    plan_namespace.some_random_plan

    do_standard_check(run_namespace.some_random_plan)
