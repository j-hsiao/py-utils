import os
import pkgutil
from importlib import import_module
import traceback
import sys


def _itermodules(paths, prefix=''):
    """Find possible modules on in dirs.

    paths: list of dirs to search.  If a file, use its dirname.
    prefix: prefix for module name (name of parent package if any)
    pkgutil docs say iter_modules might not be implemented.
    """
    if isinstance(paths, str):
        paths = [paths]
    try:
        for path in paths:
            if os.path.isfile(path):
                path = os.path.dirname(path)
            for _, name, ispkg in iter_modules(path, prefix):
                yield name
    except Exception:
        # fallback to listdir
        # .py/.pyc files, or packages, non-hidden
        for path in paths:
            path = os.path.abspath(os.path.normcase(path))
            for fname in os.listdir(path):
                name, ext = os.path.splitext(fname)
                fullpath = os.path.join(path, fname)
                if (
                        fname.startswith('_')
                        or (
                            os.path.isfile(fullpath)
                            and ext not in ('.py', '.pyc'))
                        or (
                            sys.version_info < (3,3)
                            and not os.path.exists(
                                os.path.join(fullpath, '__init__.py')))):
                    continue
                yield prefix+name

def get_subclasses(baseclass, paths, prefix=''):
    """Search for subclasses of base.

    paths: a str or seq of strs
    """
    if prefix and not prefix.endswith('.'):
        prefix += '.'
    for name in _itermodules(paths, prefix):
        try:
            module = import_module(name)
        except Exception:
            traceback.print_exc()
            continue
        try:
            keys = module.__all__
        except AttributeError:
            keys = dir(module)
        for k in keys:
            try:
                thing = getattr(module, k)
                if isinstance(thing, type) and issubclass(thing, baseclass):
                    yield thing.__name__, thing
            except Exception:
                traceback.print_exc()
