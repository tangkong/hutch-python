from types import SimpleNamespace

from pcdsdevices.sim import FastMotor, SlowMotor


def get_hw():
    """
    Create and return a standard namespace of simulated hardware.
    """
    ns = SimpleNamespace(
        fast_motor1=FastMotor(name='fast_motor1'),
        fast_motor2=FastMotor(name='fast_motor2'),
        fast_motor3=FastMotor(name='fast_motor3'),
        slow_motor1=SlowMotor(name='slow_motor1'),
        slow_motor2=SlowMotor(name='slow_motor2'),
        slow_motor3=SlowMotor(name='slow_motor3'))
    return ns
