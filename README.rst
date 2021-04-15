============
Hutch Python
============
.. image:: https://travis-ci.org/pcdshub/hutch-python.svg?branch=master
   :target: https://travis-ci.org/pcdshub/hutch-python
   :alt: Build Status

``hutch-python`` is the launcher and config reader for LCLS interactive IPython
sessions. The documentation is hosted at
`<https://pcdshub.github.io/hutch-python>`_.

Requirements
------------

This module is intended to be run using the latest pcds release in the
`pcds-envs <https://github.com/pcdshub/pcds-envs>`_ package.

This module requires Python 3.6+ and the following utilities:

- ``ipython``, for improved interactive sessions
- `pcdsdaq <https://github.com/pcdshub/pcdsdaq>`_
  for using the daq in scans
- `pcdsdevices <https://github.com/pcdshub/pcdsdevices>`_
  for our Device abstraction layers
- `elog <https://github.com/pcdshub/elog>`_
  for posting to the LCLS experiment elogs
- `happi <https://github.com/pcdshub/happi>`_
  to enable device loading from a happi database
- `psdm_qs_cli <https://github.com/slaclab/psdm_qs_cli>`_
  as an optional happi dependency for loading from the experiment
  questionnaire
- `lightpath <https://github.com/pcdshub/lightpath>`_
  organizes devices to provide a summarized state of the beamline as a whole
- ``pyyaml``, for reading config files
- ``coloredlogs``, for colored logging
- ``pyfiglet`` for hutch banners (think big ``xpppython`` on startup)
- `cookiecutter <https://github.com/audreyr/cookiecutter>`_
  for starting new hutch repos

To connect to the LCLS DAQ, your environment must have access to

- ``pydaq`` for connecting to and running the daq
- ``pycdb`` for changing daq object configurations
- ``pyami`` for viewing data from the daq

These are not available outside of the slac intranet, and in some cases
must be sync'd with the active DAQ versions, independent of all other
packages.

To automatically select the current experiment, you must run with access to
the LCLS NFS directories.

