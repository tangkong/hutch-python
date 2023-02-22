"""
Print a custom banner with some more helpful hints and information
for hutch-python sessions.

Startup script files to be run after ipython is initialized via:
``c.InteractiveTerminalApp.exec_files``

Code here will take executed after both IPython has been loaded and
the namespace has been populated with hutch objects.

These will be run as standalone python files, and should not be
imported from.
"""


from hutch_python.env_version import get_env_info

default_namespaces = ['a', 'm', 's', 'd', 'x', 'sim', 'camviewer',
                      'bp', 're']
default_objects = ['RE', 'daq', 'elog', 'archive']


def gather_hint_table(namespace: list[str]) -> str:
    """
    Gather variable name and short description into a table if the
    variable name is in the current global namespace
    """
    global_ns = globals()
    ns = [x for x in namespace if x in global_ns]

    out = ''
    for k in ns:
        out += f"  {k} - {getattr(global_ns[k], '_desc', 'N/A')}\n"

    return out


base_banner = f"""
-----------------------------------
{get_env_info()}
-----------------------------------
Helpful Namespaces:
{gather_hint_table(default_namespaces)}
Useful objects:
{gather_hint_table(default_objects)}
"""


if __name__ == '__main__':
    print(base_banner)
