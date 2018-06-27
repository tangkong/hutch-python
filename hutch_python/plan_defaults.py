from importlib import import_module
from inspect import isgeneratorfunction
from types import SimpleNamespace


def collect_plans(modules):
    """
    Take all the plans in ``modules`` and collect them into a namespace.

    Arguments
    ---------
    modules: ``list of str``
        The modules to extract plans from.
    """
    plans = {}
    for module_name in modules:
        module = import_module(module_name)
        for name, obj in module.__dict__.items():
            try:
                # Only include things that are natively from this module
                if obj.__module__ == module_name:
                    try:
                        # Check the __wrapped__ attribute for decorators
                        if isgeneratorfunction(obj.__wrapped__):
                            plans[name] = obj
                    except AttributeError:
                        # Not a decorator, check obj
                        if isgeneratorfunction(obj):
                            plans[name] = obj
            except AttributeError:
                # obj did not have __module__, probably a builtin
                pass
    return SimpleNamespace(**plans)


plans = collect_plans(['bluesky.plans'])
plan_stubs = collect_plans(['bluesky.plan_stubs'])
preprocessors = collect_plans(['bluesky.preprocessors',
                               'pcdsdaq.preprocessors'])
