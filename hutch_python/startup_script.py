"""
Initialize the ELogPoster callback and subscribe it to the RunEngine

Startup script files to be run after ipython is initialized via:
``c.InteractiveTerminalApp.exec_files``

Code here will take executed after both IPython has been loaded and
the namespace has been populated with hutch objects.

These will be run as standalone python files, and should not be
imported from.
"""


def _configure_elog_poster():
    import IPython
    from nabs.callbacks import ELogPoster

    from hutch_python.utils import safe_load

    with safe_load('ELogPoster'):
        try:
            from bluesky.run_engine import RunEngine
            from elog import HutchELog
        except ImportError:
            raise RuntimeError("A required module is missing, skip ElogPoster")

        # RE, elog will already exist by now, if not we fail and skip.
        # Some effort to give better error message for the logs.
        try:
            elog = globals()['elog']
        except KeyError:
            raise RuntimeError("elog not loaded, skip ElogPoster")
        try:
            RE = globals()['RE']
        except KeyError:
            raise RuntimeError("RE not loaded, skip ElogPoster")
        # Even if they exist, things can go wrong if the user accidentally clobbers the name
        if not isinstance(elog, HutchELog):
            raise RuntimeError("elog replaced, skip ELogPoster")
        if not isinstance(RE, RunEngine):
            raise RuntimeError("RE replaced, skip ELogPoster")

        elogc = ELogPoster(elog, IPython.get_ipython())
        RE.subscribe(elogc)


if __name__ == '__main__':
    _configure_elog_poster()
