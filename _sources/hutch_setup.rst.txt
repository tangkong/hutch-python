Hutch Setup
===========

``hutch-python`` is meant to be run in the context of a specific hutch.
Hutch repos are stored online at ``https://github.com/pcdshub/hutchname``,
and in our directory tree at ``/reg/g/pcds/pyps/apps/hutch-python/hutchname``.

If your hutch does not have a repository, you've found the correct page.

Steps to set up a Hutch
------------------------

There is a built-in template for starting a new hutch repo.
Replacing ``hutchname`` with your hutch's name:

#. ``cd /reg/g/pcds/pyps/apps/hutch-python``
#. ``hutch-python --create hutchname``
#. ``cd hutchname``
#. ``git init``
#. ``git add *``
#. ``git commit -m "ENH: Add hutchname from template"``
#. ``git remote add origin https://github.com/pcdshub/hutchname.git``
#. In a browser, navigate to `<https://github.com/pcdshub>`_ and log in.
#. Click ``New`` to make a new repo, name it ``hutchname``, do not
   initialize with README, gitignore, or license.
#. ``git push origin master``
#. As the hutch operator account, create a file named ``.qs.cfg`` in the opr's
   home area. Follow the specification of `get_qs_objs` to ensure we can load
   user objects from the questionnaire.

Updating a Hutch's Launch Scripts
---------------------------------

#. Pick up the latest environment
#. In some arbitrary directory, ``hutch-python --create hutchname``
#. Copy the generated scripts into your ``hutchname`` checkout
#. ``git checkout -b branchname``
#. git add, git commit, git push, make a PR
#. Remove your dummy ``hutchname`` directory
