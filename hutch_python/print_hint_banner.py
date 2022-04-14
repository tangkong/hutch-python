"""
Print a custom banner with some more helpful hints and information
for hutch-python sessions.
"""

import sys

from hutch_python.env_version import get_env_info

default_namespaces = ['a', 'm', 's', 'camviewer', 'bp', 're']
default_objects = ['RE', 'daq', 'elog', 'archive', ]

dirs = dir()


def filter_list(defaults):
    # I don't know why I can't use dir() inside the comprehension
    return [x for x in defaults if x in dirs]


base_banner = (
    "-----------------------------------\n"
    f'{get_env_info()}'
    "-----------------------------------\n"
    f'Helpful Namespaces: {filter_list(default_namespaces)}\n'
    f'Useful objects: {filter_list(default_objects)}\n'
)


if __name__ == '__main__':
    sys.stdout.write(base_banner)
