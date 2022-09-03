"""Provide a key for numeric sorting."""
from __future__ import print_function
__all__ = ['numsortkey']
import re
import sys
if sys.version_info.major < 3:
    range = xrange


INT = re.compile(r'(\d+)').split
FLOAT = re.compile(r'(\d+\.?\d*)').split

_inf = float('inf'),
def numsortkey(split=INT, tp=int):
    def key(string):
        """Key for numeric sort.

        Splits string into digit/non-digit via split.  Each sequence is then
        converted into a tuple of (tp, str).  This allows digit sequences to
        be compared with non-digit sequences without error.  Non-digit
        sequences will all have float('inf') as its numeric component so
        non-digit sequences should always be placed after digit sequences.
        """
        ret = split(string)
        ret[0] = (_inf, ret[0])
        for i in range(1, len(ret), 2):
            r = ret[i]
            ret[i] = (tp(r), r)
            i+=1
            ret[i] = (_inf, ret[i])
        return ret
    return key

if __name__ == '__main__':
    import os
    import argparse
    from functools import partial

    from jhsiao.tests.profile import simpletest, simpleparser
    from jhsiao.scope import Scope

    with Scope('s') as s:
        def listonly(lst):
            return list(lst)
        def normsort(lst):
            return sorted(lst)
        control = dict(s.items())
        s.update()
        def intsort(lst):
            return sorted(lst, key=numsortkey())
        def floatsort(lst):
            return sorted(lst, key=numsortkey(tp=float, split=FLOAT))

        tests = dict(s.items())

    p = argparse.ArgumentParser(parents=[simpleparser])
    p.add_argument('dirname', help='dirname to list and sort')
    args = p.parse_args()
    fnames = [_+str(i) for i, _ in enumerate(os.listdir(args.dirname))]
    fnames.append('')
    fnames.append('1234')
    fnames.append('hello')
    simpletest(control, args, (fnames,), checkmatch=None)
    simpletest(tests, args, (fnames,))
