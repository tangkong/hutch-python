"""
Module that contains general-use utilities. Some of these are useful outside of
``hutch-python``, while others are used in multiple places throughout the
module.
"""
import logging
import sys
import time
from contextlib import contextmanager
from functools import partial
from importlib import import_module
from subprocess import check_output
from types import SimpleNamespace

import pyfiglet

from .constants import (CLASS_SEARCH_PATH, CUR_EXP_SCRIPT, HUTCH_COLORS,
                        SUCCESS_LEVEL)

logging.addLevelName('SUCCESS', SUCCESS_LEVEL)
logger = logging.getLogger(__name__)
logger.success = partial(logger.log, SUCCESS_LEVEL)


@contextmanager
def safe_load(name, cls=None):
    """
    Context manager to safely run a block of code.

    This will abort running code and resume the rest of the program if
    something fails. This can be used to wrap user code with unknown behavior.
    This will log standard messages to indicate success or failure.

    Parameters
    ----------
    name: ``str``
        The name of the load to be logged. This will be used in the log
        message.

    cls: ``type``, optional
        The class of a loaded object to be logged. This will be used in the log
        message.
    """
    start_time = time.monotonic()

    if cls is None:
        identifier = name
    else:
        identifier = ' '.join((name, str(cls)))
    logger.info('Loading %s...', identifier)
    try:
        yield
        duration = time.monotonic() - start_time
        logger.success('Successfully loaded %s in %.2f s',
                       identifier, duration)
    except Exception as exc:
        duration = time.monotonic() - start_time
        logger.error('Failed to load %s after %.2f s', identifier, duration)
        logger.debug(exc, exc_info=True)


def get_current_experiment(hutch):
    """
    Get the current experiment for ``hutch``.

    This currently works by running an external script on NFS, but this will be
    changed in the future.

    Parameters
    ----------
    hutch: ``str``
        The hutch we would like to know the current experiment of

    Returns
    -------
    expname: ``str``
        Full experiment name, e.g. ``xppls2516``
    """
    script = CUR_EXP_SCRIPT.format(hutch)
    return check_output(script.split(' '), universal_newlines=True).strip('\n')


class IterableNamespace(SimpleNamespace):
    """
    ``SimpleNamespace`` that can be iterated through.

    This means we can call funtions like ``list`` on these objects to see all
    of their contents, we can put them into ``for loops``, and we can use them
    in ``generator expressions``.

    This class also has the added feature where ``len`` will correctly tell you
    the number of objects in the ``namespace``.
    """
    def __iter__(self):
        # Sorts alphabetically by key
        for _, obj in sorted(self.__dict__.items()):
            yield obj

    def __len__(self):
        return len(self.__dict__)


def count_ns_leaves(namespace):
    """
    Count the number of objects in a nested `IterableNamespace`.

    Given an `IterableNamespace` that contains other `IterableNamespace`
    objects that may in themselves contain `IterableNamespace` objects,
    determine how many non-`IterableNamespace` objects are in the tree.
    """
    count = 0
    for obj in namespace:
        if isinstance(obj, IterableNamespace):
            count += count_ns_leaves(obj)
        else:
            count += 1
    return count


def extract_objs(scope=None, skip_hidden=True, stack_offset=0):
    """
    Return all objects with the ``scope``.

    This can be though of as a ``*`` import, and it obeys the ``__all__``
    keyword functionality.

    Parameters
    ----------
    scope: ``module``, ``namespace``, or ``list`` of these, optional
        If provided, we'll import from this object.
        If omitted, we'll include all objects that have been loaded by
        hutch_python and everything in the caller's global frame.

    skip_hidden: ``bool``, optional
        If ``True``, we'll omit objects with leading underscores.

    stack_offset: ``int``, optional
        If ``scope`` was not provided, we'll use ``stack_offset`` to determine
        which frame is the user's frame. Leave this at zero if you want the
        objects in the caller's frame, and increase it by one for each level
        up the stack your frame is.

    Returns
    -------
    objs: ``dict``
        Mapping from name in scope to object
    """
    if scope is None:
        stack_depth = 1 + stack_offset
        frame = sys._getframe(stack_depth)
        try:
            objs = extract_objs(scope='hutch_python.db',
                                skip_hidden=skip_hidden,
                                stack_offset=stack_offset)
        except ImportError:
            objs = {}
        objs.update(frame.f_globals)
    else:
        if isinstance(scope, list):
            objs = {}
            for s in scope:
                objs.update(extract_objs(scope=s,
                                         skip_hidden=skip_hidden,
                                         stack_offset=stack_offset))
        else:
            if isinstance(scope, str):
                if scope.endswith('.py'):
                    scope = scope[:-3]
                scope = import_module(scope)
            objs = scope.__dict__.copy()

    all_kwd = objs.get('__all__')
    if all_kwd is None:
        if skip_hidden:
            return {k: v for k, v in objs.items() if k[0] != '_'}
        else:
            return objs
    else:
        all_objs = {}
        for kwd in all_kwd:
            all_objs[kwd] = objs.get(kwd)
        return all_objs


def find_object(obj_path):
    """
    Given a string module path to an object, return that object.

    Parameters
    ----------
    obj_path: ``str``
        String module path to an object

    Returns
    -------
    obj: ``object``
        That object
    """
    parts = obj_path.split('.')
    module_path = '.'.join(parts[:-1])
    class_name = parts[-1]
    module = import_module(module_path)
    return getattr(module, class_name)


def find_class(class_path, check_defaults=True):
    """
    Find a ``type`` object given a ``str``.

    Given a string class name, either return the matching built-in type or
    import the correct module and return the type.

    Parameters
    ----------
    class_path: ``str``
        Built-in type name or import path e.g. ``ophyd.device.Device``

    check_defaults: ``bool``
        If ``True``, try checking inside each module in ``CLASS_SEARCH_PATH``

    Returns
    -------
    cls: ``type``
        The class we found
    """
    try:
        if '.' in class_path:
            return find_object(class_path)
        else:
            return eval(class_path)
    except NameError:
        if check_defaults:
            for default in CLASS_SEARCH_PATH:
                try:
                    return find_class(default + '.' + class_path,
                                      check_defaults=False)
                except AttributeError:
                    pass
        raise ImportError('Could not find_class for {}'.format(class_path))


def strip_prefix(name, strip_text):
    """
    Strip the first section of an underscore-separated ``name``.

    If the first section matches the ``strip_text``, we'll remove it.
    Otherwise, the object will remain unchanged.

    Parameters
    ----------
    name: ``str``
        underscore_separated_name to strip from

    strip_text: ``str``
        Text to strip from the name, if it matches the first segment

    Returns
    -------
    stripped: ``str``
        The ``name``, modified or unmodified.
    """
    if name.startswith(strip_text):
        return name[len(strip_text)+1:]
    else:
        return name


def maybe_exit(logger, message, exception_message, *, exit_code=1):
    """
    For potentially fatal exceptions, prompt the user whether or not to exit.

    This outputs a full exception traceback first with the message
    `exception_message`, before a friendlier `message`, and then querying the
    user.

    Parameters
    ----------
    logger : logging.Logger
        The logger instance to output a message.

    message : str
        The user-friendly error message.

    exception_message : str
        The error to show along with the full exception traceback.

    exit_code : int, optional
        The exit code, if the user decides to exit.
    """
    logger.exception(exception_message)
    logger.error(message)

    response = input('Continue loading hutch-python? [Yn] ')
    if response.lower() not in {'y', ''}:
        sys.exit(exit_code)


def hutch_banner(hutch_name='Hutch '):
    """
    Display the hutch's banner.

    Parameters
    ----------
    hutch_name: ``str``
        Name of the hutch to produce a banner for.
    """
    text = hutch_name + 'Python'
    f = pyfiglet.Figlet(font='big')
    banner = f.renderText(text)
    if hutch_name in HUTCH_COLORS:
        banner = '\x1b[{}m'.format(HUTCH_COLORS[hutch_name]) + banner
    print(banner)
