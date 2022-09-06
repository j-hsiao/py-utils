import os
def fdir(base=None, *modifiers):
    """Convenience function to full dirname.

    If base is None, use inspect to find the filename of caller.
    If base is a file, then use its directory.  Otherwise, just use base
    as is.  modifiers will be joined onto the base.
    """
    if name is None:
        import inspect
        name = inspect.currentframe().f_back.f_code.co_filename
    fullpath = os.path.abspath(name)
    if not os.path.isdir(fullpath):
        fullpath = os.path.dirname(fullpath)
    return os.path.join(fullpath, *modifiers)
