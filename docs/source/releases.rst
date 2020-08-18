Release History
###############

v1.4.0 (2020-08-18)
===================

Features
--------
- Load hutch-python with engineering mode disabled to optimize interactive
  use.


v1.3.1 (2020-07-27)
===================

Fixes and Maintenance
---------------------
- Test suite update for compatibility with lightpath v0.6.5


v1.3.0 (2020-07-01)
===================

Features
--------
- Pack camviewer config into a camviewer namespace for ease of access
  and to avoid name collisions with other data sources.


v1.2.3 (2020-05-29)
===================

Fixes and Maintenance
---------------------
- Fix issue with tests freezing


v1.2.2 (2020-05-21)
===================

Fixes and Maintenance
---------------------
- Fix issue with generated area detectors having the wrong prefix


v1.2.1 (2020-05-21)
===================

Fixes and Maintenance
---------------------
- Fix issue preventing conda upload on tag


v1.2.0 (2020-05-21)
===================

Features
--------
- Configure the logstash logger using ``pcdsutils``

Fixes and Maintenance
---------------------
- Adjust for latest ``happi`` API
- Add documentation about logstash logging
- Hush the noisiest loggers that are spamming the terminal sessions


v1.1.1 (2020-02-05)
===================

Fixes and Maintenance
---------------------
- Make tests compatible with ``ophyd`` ``v1.1.1``
- Small adjustments to remove some warnings
- Small updates to hutch directory generator

v1.1.0 (2020-01-10)
===================

Features
--------
- Add ``archapp`` support. Check out the ``archive`` object in the hutch
  python namespace for access to the archiver appliance data.

v1.0.1 (2019-03-08)
===================

Fixes and Maintenance
---------------------
- Clean up code for the ``hutch-python`` launcher
- Fix issues with the test suite
- Fix issues with automatically loading ipython profiles

v1.0.0 (2018-10-12)
===================

API Breaks
----------
- Swap to the newer ``psdm_qs_cli`` API for experiment loading that is
  compatible with commissioning experiment names.

v0.7.0 (2018-08-06)
===================

Features
--------
- Add a `ScanVars` class for the legacy scan pvs tie-in.
- Automatically load all cameras defined in the camviewer config file.
- Add the ``--exp`` arg for forcing the active experiment for the duration
  of a session.

Bugfixes
--------
- Exclude having a beampath when there are no devices on the path.
  This is because the resulting empty path causes issues in the
  environment. This will most commonly occur when calling
  ``hutch-python`` with no arguments.

Misc
----
- Fix a few typos

v0.6.0 (2018-05-27)
===================

Features
--------
- Provide well-curated namespaces for ``bluesky`` plans. These are in the
  shell as ``bp`` (bluesky plans) for normal plans, ``bps`` (bluesky plan
  stubs) for plans that are not complete on their own, and ``bpp``
  (bluesky plan preprocessors) for plans that modify other plans.

Bugfixes
---------
- Show a correct error message when there is an ``ImportError`` in an
  experiment file. This previously assumed the ``ImportError`` was from
  a missing experiment file. (#126)
- Prevent duplicate names in `tree_namespace` from breaking the tree.
  Show a relevant warning message. (#128)
- Do not configure the ``matplotlib`` backend for IPython if a user does not
  have a valid ``$DISPLAY`` environment variable. The most common case of this
  is if X-Forwarding is disabled. (#132)

v0.5.0 (2018-05-08)
===================

Bugfixes
---------
- fix issue where importing hutchname.db could break under certain conditions
- fix issue where autocompleting a ``SimpleNamespace`` subclass would always
  have an extra mro() method, even though this is a class method not shared
  with instances.
- add logs folder to the hutch-python directory creator

API Changes
-----------
- ``metadata_namespace`` renamed to `tree_namespace`

v0.4.0 (2018-04-23)
===================

Features
--------
- ``elog`` object and posting
- load devices upstream from the hutch along the light path

Bugfixes
--------
- Allow posting bug reports to github from the control room machines through the proxy
- Optimize the namespaces for faster loads and avoid a critical slowdown bug
- Make hutch banner as early as possible to avoid errant log messages in front of the banner
- Make cxi's banner red, as was intended
- hutch template automatically picks the latest environment, instead of hard-coding it

v0.3.0 (2018-04-06)
===================

Features
--------
- In-terminal bug reporting
- Port of the old python presets system
- Objects from the questionnaire are included in the experiment object
- Experiment object is always included

Bugfixes
--------
- No longer create 1-item metadata objects
- ``db.txt`` is created in all-write mode

API Changes
-----------
- Daq platform map is no longer stored in the module, this now must be configured
  through ``conf.yml`` for nonzero platforms.

Minor Changes
-------------
- ``qs.cfg`` renamed to ``web.cfg``, with backwards compatibility
