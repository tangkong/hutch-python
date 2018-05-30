Release History
###############

Next Release
============

Bugfixes
---------
- Show a correct error message when there is an ``ImportError`` in an
  experiment file. This previously assumed the ``ImportError`` was from
  a missing experiment file. (#126)
- Prevent duplicate names in `tree_namespace` from breaking the tree.
  Show a relevant warning message. (#128)

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
- `metadata_namespace` renamed to `tree_namespace`

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
