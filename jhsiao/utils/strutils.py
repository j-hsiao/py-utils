__all__ = ['splitlines', 'unindent']

from itertools import chain, islice

def splitlines(line, width=72, delim=' '):
    """Split a line on on delims to fit in width.

    Assume no newlines.  Return a list of lines.
    """
    idx = line.find(delim)
    if idx < 0:
        return line
    while 1:
        nidx = line.find(' ', idx+1)
        if 0 <= nidx < width:
            idx = nidx
        else:
            curline = line[:idx]
            remain = line[idx+1:]
            if not remain:
                return [curline]
            elif nidx < 0:
                return [curline, remain]
            else:
                l = [curline]
                l.extend(splitlines(remain, width))
                return l

def unindent(docstr):
    """Unindents docstring.

    https://peps.python.org/pep-0257/ for docstr handling.
    """
    docstr = docstr.strip()
    lines = docstr.splitlines()
    best = len(docstr)
    for line in islice(lines, 1, None):
        stripped = line.lstrip()
        if stripped:
            l = len(line) - len(stripped)
            if l < best:
                best = l
    if best < len(docstr):
        ret = [lines[0].rstrip()]
        for line in islice(lines, 1, None):
            ret.append(line[best:].rstrip())
        return '\n'.join(ret)
    else:
        return docstr

def longest_fmt(strs):
    """Return a callable to format str to longest length."""
    return '{{:{}}}'.format(max(map(len, strs))).format
