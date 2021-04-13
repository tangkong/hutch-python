from pcdsdevices.sim import FastMotor, SlowMotor

from .utils import HelpfulNamespace


def get_hw():
    """
    Create and return a standard namespace of simulated hardware.
    """
    ns = HelpfulNamespace(
        fast_motor1=FastMotor(name='fast_motor1'),
        fast_motor2=FastMotor(name='fast_motor2'),
        fast_motor3=FastMotor(name='fast_motor3'),
        slow_motor1=SlowMotor(name='slow_motor1'),
        slow_motor2=SlowMotor(name='slow_motor2'),
        slow_motor3=SlowMotor(name='slow_motor3'))
    return ns
