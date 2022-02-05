from typing import Callable

import pytest
from bluesky import RunEngine
from bluesky.plan_stubs import null, pause
from bluesky.plans import scan
from bluesky.utils import RunEngineInterrupted
from ophyd.sim import motor

from hutch_python.run_engine_wrapper import (run_engine_wrapper,
                                             run_scan_namespace)
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


def test_run_scan_namespace(RE: RunEngine):
    normal_ns = HelpfulNamespace(scan=scan)
    run_ns = run_scan_namespace(RE, normal_ns)
    do_standard_check(run_ns.scan)
