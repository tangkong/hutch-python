from importlib import import_module

from . import utils


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
                from_module = obj.__module__ == module_name
                # Only include callables
                is_callable = callable(obj)
                # Skip hidden items
                is_hidden = len(name) == 0 or name[0] == '_'

                if from_module and is_callable and not is_hidden:
                    plans[name] = obj
            except AttributeError:
                # obj did not have __module__, probably a builtin
                pass
    return utils.HelpfulNamespace(**plans)


plans = collect_plans(['bluesky.plans',
                       'nabs.plans'])
plan_stubs = collect_plans(['bluesky.plan_stubs',
                            'nabs.plan_stubs'])
preprocessors = collect_plans(['bluesky.preprocessors',
                               'nabs.preprocessors'])
