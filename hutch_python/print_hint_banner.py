"""
Print a custom banner with some more helpful hints and information
for hutch-python sessions.
"""

import sys

from hutch_python.env_version import get_env_info

default_namespaces = ['a', 'm', 's', 'd', 'x', 'sim', 'camviewer',
                      'bp', 're']
default_objects = ['RE', 'daq', 'elog', 'archive']


def gather_hint_table(namespace):
    """
    Gather variable name and short description into a table if the
    variable name is in the current global namespace
    """
    global_ns = globals()
    ns = [x for x in namespace if x in global_ns.keys()]

    out = ''
    for k in ns:
        out += f"  {k} - {getattr(global_ns[k], '_desc', 'N/A')}\n"

    return out


base_banner = (
    "-----------------------------------\n"
    f'{get_env_info()}'
    "-----------------------------------\n"
    f'Helpful Namespaces:\n'
    f'{gather_hint_table(default_namespaces)}\n'
    f'Useful objects:\n'
    f'{gather_hint_table(default_objects)}\n'
)


if __name__ == '__main__':
    sys.stdout.write(base_banner)
