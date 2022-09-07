from __future__ import print_function, division
import sys

from jhsiao.utils.linkedlist import Links
import traceback

import random

def eq(l, check):
    return l == check and list(l) == check

def test_append():
    l = Links()
    check = list(range(10))
    for i, v in enumerate(check):
        l.append(v)
        assert eq(l, check[:i+1])

    l.append(1, l.first)
    check.insert(1, 1)
    assert eq(l, check)

    l.append(1, l(3))
    check.insert(4, 1)
    assert eq(l, check)

    l.appendleft(69, l(0))
    check.insert(0, 69)
    assert eq(l, check)

    l.appendleft(42, l(-1))
    check.insert(-1, 42)
    assert eq(l, check)

def test_shift():
    """Shifting from a link."""
    l = Links(range(10))
    for i in range(-10, 10):
        cur = l(i)
        if i < 0:
            trui = i + len(l)
        else:
            trui = i
        assert (cur >> (-1 - trui)) is None
        assert (cur >> (11 - trui)) is None
        for j in range(0, 10):
            assert (cur >> (j-trui))() == j

def test_indexing():
    """Testing [] notation."""
    check = list(range(10))
    l = Links(check)
    for i in range(-10, 10):
        assert l[i] == check[i]
        assert l(i)() == check[i]

def test_pop():
    check = list(range(10))
    l = Links(check)
    assert check.pop() == l.pop()()
    assert eq(l, check)
    while l:
        pick = random.randint(0, len(l)-1)
        assert check.pop(pick) == l.pop(l(pick))()
        assert eq(l, check)

def test_extend():
    l = Links()
    check = []
    l.extend(b'hello')
    check.extend(b'hello')
    assert eq(l, check)

    l.extend(b'hello')
    check.extend(b'hello')
    assert eq(l, check)

    l.insert(l(0), 'hello')
    check = list('hello') + check
    assert eq(l, check)

    l.extendleft('whatever')
    check = list(reversed('whatever')) + check
    assert eq(l, check)

    l.insert(l(0), '')
    assert eq(l, check)


def test_clear():
    check = list(range(10))
    l = Links(check)
    links = list(l.links())
    assert eq(l, check)
    l.clear()
    assert eq(l, [])
    assert all(_[:2] == [None]*2 for _ in links)

def test_slicing():
    check = list(range(10))
    l = Links(check)
    for start in range(-10, 10):
        for stop in range(-10, 10):
            for step in range(-10, 10):
                if step == 0:
                    step = None
                assert list(l[start:stop:step]) == check[start:stop:step]
    assert l[:] == l
    assert l[:] is not l
    for i, (l1, l2) in enumerate(zip(l[:].links(), l.links())):
        assert l1 is not l2
        assert l1() is l2()

    assert i == len(l)-1

    assert eq(l[l.first:5], l[:5]) and eq(l[:5], check[:5])
    assert eq(l[l.last:-5], l[-1:-6:-1]) and eq(l[-1:-6:-1], check[-1:-6:-1])

    l[:2] = ()
    check[:2] = ()
    assert eq(l, check)

    l[-2:] = 'ab'
    check[-2:] = 'ab'
    assert eq(l, check)

    l[-2:] = 'cdef'
    check[-2:] = 'cdef'
    assert eq(l, check)

    l[2:4] = 'hijk'
    check[2:4] = 'hijk'
    assert eq(l, check)

    l[2:4] = 'l'
    check[2:4] = 'l'
    assert eq(l, check)

    l[::2] = range(0, len(l), 2)
    check[::2] = range(0, len(check), 2)
    assert eq(l, check)

    start, stop, step = slice(None,None,-2).indices(len(l))
    l[::-2] = range(start, stop, step)
    check[::-2] = range(start, stop, step)
    assert eq(l, check)

    start, stop, step = slice(None,None,-2).indices(len(l))
    try:
        l[::-3] = range(start, stop, step)
    except ValueError:
        pass
    else:
        raise Exception('should have errored')
    try:
        check[::-3] = range(start, stop, step)
    except ValueError:
        pass
    else:
        raise Exception('should have errored')
    assert eq(l, check)

    links = list(l.links())
    l[:] = ()
    check[:] = ()
    assert eq(l, check)
    assert all(lnk == [None,None,None] for lnk in links)


def run(tests):
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument(
        'test', nargs='?',
        choices=[k[5:] for k in tests])
    args = p.parse_args()
    if args.test:
        k = 'test_{}'.format(args.test)
        tests = {k: tests[k]}
    for k, v in tests.items():
        print(k, end='\t: ', file=sys.stderr)
        sys.stderr.flush()
        try:
            v()
        except Exception:
            traceback.print_exc()
            return
        print('pass')
if __name__ == '__main__':
    run({k:v for k,v in locals().items() if k.startswith('test_')})
